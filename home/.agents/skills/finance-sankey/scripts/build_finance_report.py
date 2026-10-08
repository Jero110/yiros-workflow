#!/usr/bin/env python3
"""Builds a private spending report and standalone SVG Sankey from normalized CSV."""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import decimal
import html
import json
import pathlib
import typing
from collections.abc import Mapping, Sequence


EXCLUDED_TYPES = frozenset({"transfer", "card_payment", "duplicate"})
EXPENSE_TYPES = frozenset({"expense", "fee", "unknown"})
COLORS = (
    "#7C3AED",
    "#2563EB",
    "#0891B2",
    "#059669",
    "#65A30D",
    "#CA8A04",
    "#EA580C",
    "#DC2626",
    "#DB2777",
    "#9333EA",
    "#475569",
    "#0F766E",
)


def _parse_amount(raw_amount: str) -> decimal.Decimal:
    """Parses an amount from the normalized input format.

    Args:
        raw_amount: Decimal amount using a dot as the preferred separator.

    Returns:
        Parsed decimal amount.

    Raises:
        ValueError: If the amount is empty or malformed.
    """
    value = raw_amount.strip().replace(" ", "")
    if not value:
        raise ValueError("amount is empty")
    if "," in value and "." not in value:
        value = value.replace(",", ".")
    try:
        return decimal.Decimal(value)
    except decimal.InvalidOperation as error:
        raise ValueError(f"invalid amount: {raw_amount!r}") from error


def _read_transactions(path: pathlib.Path) -> list[dict[str, str | decimal.Decimal]]:
    """Reads and validates normalized transaction rows."""
    required = {"date", "description", "amount"}
    rows: list[dict[str, str | decimal.Decimal]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"missing required CSV columns: {names}")
        for line_number, source_row in enumerate(reader, start=2):
            if not any(source_row.values()):
                continue
            row: dict[str, str | decimal.Decimal] = {
                key: (value or "").strip() for key, value in source_row.items()
            }
            try:
                row["amount"] = _parse_amount(str(row["amount"]))
                dt.date.fromisoformat(str(row["date"]))
            except ValueError as error:
                raise ValueError(f"line {line_number}: {error}") from error
            rows.append(row)
    if not rows:
        raise ValueError("the CSV contains no transaction rows")
    return rows


def _expense_value(row: Mapping[str, str | decimal.Decimal]) -> decimal.Decimal:
    """Returns positive spending contribution, including categorized refunds."""
    amount = row["amount"]
    if not isinstance(amount, decimal.Decimal):
        raise TypeError("normalized amount is not Decimal")
    transaction_type = str(row.get("transaction_type", "unknown")).lower()
    if transaction_type in EXCLUDED_TYPES or transaction_type == "income":
        return decimal.Decimal(0)
    if transaction_type == "refund":
        return -amount if row.get("category") else decimal.Decimal(0)
    if amount < 0 and transaction_type in EXPENSE_TYPES:
        return -amount
    return decimal.Decimal(0)


def _aggregate(
    rows: Sequence[Mapping[str, str | decimal.Decimal]],
) -> dict[str, object]:
    """Aggregates transactions into auditable report metrics."""
    categories: collections.defaultdict[str, decimal.Decimal] = collections.defaultdict(
        decimal.Decimal
    )
    subcategories: collections.defaultdict[
        tuple[str, str], decimal.Decimal
    ] = collections.defaultdict(decimal.Decimal)
    merchants: collections.defaultdict[
        tuple[str, str], decimal.Decimal
    ] = collections.defaultdict(decimal.Decimal)
    excluded: collections.defaultdict[str, decimal.Decimal] = collections.defaultdict(
        decimal.Decimal
    )
    income = decimal.Decimal(0)
    included_count = 0
    uncertain_count = 0

    for row in rows:
        amount = row["amount"]
        if not isinstance(amount, decimal.Decimal):
            continue
        transaction_type = str(row.get("transaction_type", "unknown")).lower()
        if transaction_type in EXCLUDED_TYPES:
            excluded[transaction_type] += abs(amount)
            continue
        if transaction_type == "income" and amount > 0:
            income += amount
            continue

        spending = _expense_value(row)
        if not spending:
            continue
        category = str(row.get("category") or "Sin clasificar")
        subcategory = str(row.get("subcategory") or "Sin detalle")
        merchant = str(row.get("merchant") or row.get("description") or "Sin comercio")
        categories[category] += spending
        subcategories[(category, subcategory)] += spending
        merchants[(category, merchant)] += spending
        included_count += 1
        if str(row.get("confidence", "")).lower() == "low" or category == "Sin clasificar":
            uncertain_count += 1

    categories = collections.defaultdict(
        decimal.Decimal, {key: value for key, value in categories.items() if value > 0}
    )
    subcategories = collections.defaultdict(
        decimal.Decimal,
        {key: value for key, value in subcategories.items() if value > 0},
    )
    total_spending = sum(categories.values(), decimal.Decimal(0))
    dates = [str(row["date"]) for row in rows]
    return {
        "period_start": min(dates),
        "period_end": max(dates),
        "transaction_count": len(rows),
        "included_count": included_count,
        "uncertain_count": uncertain_count,
        "income": income,
        "total_spending": total_spending,
        "net": income - total_spending,
        "categories": dict(categories),
        "subcategories": dict(subcategories),
        "merchants": dict(merchants),
        "excluded": dict(excluded),
    }


def _money(value: decimal.Decimal, currency: str) -> str:
    """Formats money consistently without relying on system locale."""
    quantized = value.quantize(decimal.Decimal("0.01"))
    return f"{quantized:,.2f} {currency}".replace(",", "_").replace(".", ",").replace("_", ".")


def _json_decimal(value: object) -> object:
    if isinstance(value, decimal.Decimal):
        return float(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _sorted_values(values: Mapping[str, decimal.Decimal]) -> list[tuple[str, decimal.Decimal]]:
    return sorted(values.items(), key=lambda item: (-item[1], item[0].casefold()))


def _build_markdown(summary: Mapping[str, object], currency: str) -> str:
    """Builds the quantitative Markdown report."""
    spending = summary["total_spending"]
    income = summary["income"]
    net = summary["net"]
    if not isinstance(spending, decimal.Decimal):
        raise TypeError("total_spending must be Decimal")
    if not isinstance(income, decimal.Decimal):
        raise TypeError("income must be Decimal")
    if not isinstance(net, decimal.Decimal):
        raise TypeError("net must be Decimal")
    raw_categories = summary["categories"]
    raw_merchants = summary["merchants"]
    raw_excluded = summary["excluded"]
    if not isinstance(raw_categories, dict) or not isinstance(raw_merchants, dict):
        raise TypeError("summary aggregates are malformed")
    categories = typing.cast(dict[str, decimal.Decimal], raw_categories)
    merchants = typing.cast(
        dict[tuple[str, str], decimal.Decimal], raw_merchants
    )
    excluded = typing.cast(dict[str, decimal.Decimal], raw_excluded)

    lines = [
        "# Informe de gastos",
        "",
        "## Resumen ejecutivo",
        "",
        f"- Periodo: {summary['period_start']} a {summary['period_end']}",
        f"- Gastos incluidos: **{_money(spending, currency)}**",
        f"- Ingresos observados: **{_money(income, currency)}**",
        f"- Balance neto observado: **{_money(net, currency)}**",
        f"- Movimientos: {summary['transaction_count']} totales; "
        f"{summary['included_count']} incluidos en gastos; "
        f"{summary['uncertain_count']} con clasificación incierta.",
        "",
        "## A dónde se fue el dinero",
        "",
        "| Categoría | Importe | % del gasto |",
        "|---|---:|---:|",
    ]
    for category, value in _sorted_values(categories):
        percentage = (value / spending * 100) if spending else decimal.Decimal(0)
        lines.append(f"| {category} | {_money(value, currency)} | {percentage:.1f}% |")

    lines.extend(["", "## Principales comercios por categoría", ""])
    grouped_merchants: collections.defaultdict[
        str, list[tuple[str, decimal.Decimal]]
    ] = collections.defaultdict(list)
    for key, value in merchants.items():
        category, merchant = key
        grouped_merchants[category].append((merchant, value))
    for category, _ in _sorted_values(categories):
        lines.append(f"### {category}")
        for merchant, value in sorted(
            grouped_merchants[category], key=lambda item: (-item[1], item[0].casefold())
        )[:10]:
            lines.append(f"- {merchant}: {_money(value, currency)}")
        lines.append("")

    lines.extend(["## Movimientos excluidos", ""])
    if isinstance(excluded, dict) and excluded:
        for transaction_type, value in _sorted_values(excluded):
            lines.append(f"- {transaction_type}: {_money(value, currency)}")
    else:
        lines.append("No se identificaron transferencias, pagos de tarjeta o duplicados excluidos.")
    lines.extend(
        [
            "",
            "## Por revisar",
            "",
            f"Hay {summary['uncertain_count']} movimientos con confianza baja o sin clasificar.",
            "",
            "## Metodología y límites",
            "",
            "Los gastos usan importes negativos; las transferencias internas y pagos de tarjeta "
            "se excluyen. Los reembolsos categorizados reducen la categoría correspondiente. "
            "Revisar las clasificaciones inciertas antes de tomar decisiones.",
            "",
        ]
    )
    return "\n".join(lines)


def _ribbon_path(
    x_start: float,
    y_start: float,
    x_end: float,
    y_end: float,
    thickness: float,
) -> str:
    """Creates a smooth SVG ribbon path."""
    control_one = x_start + (x_end - x_start) * 0.45
    control_two = x_start + (x_end - x_start) * 0.55
    return (
        f"M {x_start:.1f},{y_start:.1f} "
        f"C {control_one:.1f},{y_start:.1f} {control_two:.1f},{y_end:.1f} "
        f"{x_end:.1f},{y_end:.1f} "
        f"L {x_end:.1f},{y_end + thickness:.1f} "
        f"C {control_two:.1f},{y_end + thickness:.1f} "
        f"{control_one:.1f},{y_start + thickness:.1f} "
        f"{x_start:.1f},{y_start + thickness:.1f} Z"
    )


def _build_sankey_svg(summary: Mapping[str, object], currency: str) -> str:
    """Builds a proportional three-column spending Sankey as SVG."""
    raw_categories = summary["categories"]
    raw_subcategories = summary["subcategories"]
    total = summary["total_spending"]
    if not isinstance(raw_categories, dict) or not isinstance(raw_subcategories, dict):
        raise TypeError("summary aggregates are malformed")
    if not isinstance(total, decimal.Decimal) or total <= 0:
        return '<p class="empty">No hay gastos incluidos para dibujar.</p>'
    categories = typing.cast(dict[str, decimal.Decimal], raw_categories)
    subcategories = typing.cast(
        dict[tuple[str, str], decimal.Decimal], raw_subcategories
    )

    category_items = _sorted_values(categories)
    child_map: collections.defaultdict[
        str, list[tuple[str, decimal.Decimal]]
    ] = collections.defaultdict(list)
    for key, value in subcategories.items():
        category, subcategory = key
        child_map[category].append((subcategory, value))
    for children in child_map.values():
        children.sort(key=lambda item: (-item[1], item[0].casefold()))

    child_count = max(1, sum(len(items) for items in child_map.values()))
    height = max(720, child_count * 28 + len(category_items) * 12 + 100)
    top = 48.0
    bottom = height - 48.0
    category_gap = 14.0
    child_gap = 7.0
    available = bottom - top - category_gap * max(0, len(category_items) - 1)
    scale = available / float(total)

    root_x, category_x, child_x = 70.0, 480.0, 900.0
    node_width = 18.0
    root_height = float(total) * scale
    root_y = top
    category_positions: dict[str, tuple[float, float, str]] = {}
    category_ids: dict[str, str] = {}
    category_cursor = top
    root_cursor = top
    ribbons: list[str] = []
    nodes: list[str] = []
    labels: list[str] = []

    for index, (category, value) in enumerate(category_items):
        thickness = float(value) * scale
        color = COLORS[index % len(COLORS)]
        category_positions[category] = (category_cursor, thickness, color)
        category_ids[category] = f"category-{index}"
        path = _ribbon_path(
            root_x + node_width,
            root_cursor,
            category_x,
            category_cursor,
            thickness,
        )
        detail_id = category_ids[category]
        ribbons.append(
            f'<path d="{path}" fill="{color}" fill-opacity="0.42" '
            f'class="category-flow" data-category-target="#{detail_id}" '
            f'tabindex="0" role="button"><title>Ver transacciones de '
            f'{html.escape(category)}: {html.escape(_money(value, currency))}'
            f"</title></path>"
        )
        root_cursor += thickness
        category_cursor += thickness + category_gap

    child_cursor = top
    for category, _ in category_items:
        category_y, category_height, color = category_positions[category]
        detail_id = category_ids[category]
        source_cursor = category_y
        for subcategory, value in child_map[category]:
            thickness = float(value) * scale
            path = _ribbon_path(
                category_x + node_width,
                source_cursor,
                child_x,
                child_cursor,
                thickness,
            )
            ribbons.append(
                f'<path d="{path}" fill="{color}" fill-opacity="0.32" '
                f'class="category-flow" data-category-target="#{detail_id}" '
                f'tabindex="0" role="button"><title>Ver transacciones de '
                f'{html.escape(category)} → {html.escape(subcategory)}: '
                f'{html.escape(_money(value, currency))}</title></path>'
            )
            nodes.append(
                f'<rect x="{child_x}" y="{child_cursor:.1f}" width="{node_width}" '
                f'height="{max(thickness, 1):.1f}" rx="4" fill="{color}"/>'
            )
            if thickness >= 9:
                label_y = child_cursor + thickness / 2 + 4
                labels.append(
                    f'<text x="{child_x + node_width + 9}" y="{label_y:.1f}" '
                    f'class="node-label">{html.escape(subcategory)} · '
                    f'{html.escape(_money(value, currency))}</text>'
                )
            source_cursor += thickness
            child_cursor += thickness + child_gap
        nodes.append(
            f'<a href="#{detail_id}" aria-label="Ver transacciones de '
            f'{html.escape(category)}"><rect x="{category_x}" y="{category_y:.1f}" '
            f'width="{node_width}" height="{max(category_height, 1):.1f}" '
            f'rx="4" fill="{color}"/></a>'
        )
        labels.append(
            f'<a href="#{detail_id}" aria-label="Ver transacciones de '
            f'{html.escape(category)}"><text x="{category_x - 10}" '
            f'y="{category_y + category_height / 2 + 4:.1f}" '
            f'class="category-label" text-anchor="end">'
            f'{html.escape(category)}</text></a>'
        )

    nodes.append(
        f'<rect x="{root_x}" y="{root_y:.1f}" width="{node_width}" '
        f'height="{root_height:.1f}" rx="4" fill="#111827"/>'
    )
    labels.append(
        f'<text x="{root_x - 10}" y="{root_y + root_height / 2:.1f}" '
        f'class="root-label" text-anchor="end">Gasto total</text>'
    )
    return (
        f'<svg viewBox="0 0 1200 {height}" role="img" '
        f'aria-label="Flujo del gasto total hacia categorías y subcategorías">'
        + "".join(ribbons)
        + "".join(nodes)
        + "".join(labels)
        + "</svg>"
    )


def _build_transaction_details(
    summary: Mapping[str, object],
    rows: Sequence[Mapping[str, str | decimal.Decimal]],
    currency: str,
) -> str:
    """Builds expandable, auditable transaction tables for each category."""
    raw_categories = summary["categories"]
    if not isinstance(raw_categories, dict):
        raise TypeError("summary categories are malformed")
    categories = typing.cast(dict[str, decimal.Decimal], raw_categories)
    grouped: collections.defaultdict[
        str, list[tuple[Mapping[str, str | decimal.Decimal], decimal.Decimal]]
    ] = collections.defaultdict(list)
    for row in rows:
        contribution = _expense_value(row)
        if contribution:
            category = str(row.get("category") or "Sin clasificar")
            grouped[category].append((row, contribution))

    sections: list[str] = []
    for index, (category, total) in enumerate(_sorted_values(categories)):
        transaction_rows: list[str] = []
        category_rows = sorted(
            grouped[category],
            key=lambda item: (
                str(item[0].get("date", "")),
                str(item[0].get("merchant", "")).casefold(),
            ),
        )
        for row, contribution in category_rows:
            confidence = str(row.get("confidence") or "—")
            notes = str(row.get("notes") or "")
            transaction_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row.get('date', '')))}</td>"
                f"<td>{html.escape(str(row.get('merchant') or 'Sin comercio'))}</td>"
                f"<td>{html.escape(str(row.get('description') or ''))}</td>"
                f"<td>{html.escape(str(row.get('account') or ''))}</td>"
                f"<td>{html.escape(_money(contribution, currency))}</td>"
                f"<td>{html.escape(confidence)}</td>"
                f"<td>{html.escape(notes)}</td>"
                "</tr>"
            )
        sections.append(
            f'<details class="category-detail" id="category-{index}">'
            f"<summary><span>{html.escape(category)}</span>"
            f"<strong>{html.escape(_money(total, currency))}</strong></summary>"
            '<div class="table-wrap"><table><thead><tr>'
            "<th>Fecha</th><th>Comercio</th><th>Descripción original</th>"
            "<th>Cuenta</th><th>Impacto en gasto</th><th>Confianza</th>"
            "<th>Notas</th></tr></thead>"
            f"<tbody>{''.join(transaction_rows)}</tbody></table></div></details>"
        )
    return "".join(sections)


def _build_html(
    summary: Mapping[str, object],
    currency: str,
    rows: Sequence[Mapping[str, str | decimal.Decimal]],
) -> str:
    """Builds a standalone HTML report containing the Sankey chart."""
    category_rows = []
    raw_categories = summary["categories"]
    total = summary["total_spending"]
    income = summary["income"]
    net = summary["net"]
    if not isinstance(raw_categories, dict) or not isinstance(total, decimal.Decimal):
        raise TypeError("summary aggregates are malformed")
    if not isinstance(income, decimal.Decimal) or not isinstance(net, decimal.Decimal):
        raise TypeError("summary totals must be Decimal")
    categories = typing.cast(dict[str, decimal.Decimal], raw_categories)
    for category, value in _sorted_values(categories):
        percentage = (value / total * 100) if total else decimal.Decimal(0)
        category_rows.append(
            "<tr>"
            f"<td>{html.escape(category)}</td>"
            f"<td>{html.escape(_money(value, currency))}</td>"
            f"<td>{percentage:.1f}%</td>"
            "</tr>"
        )
    sankey = _build_sankey_svg(summary, currency)
    transaction_details = _build_transaction_details(summary, rows, currency)
    generated = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flujo de gastos</title>
<style>
:root {{ color-scheme: light; --ink:#111827; --muted:#64748b; --paper:#f8fafc; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif; }}
main {{ max-width:1440px; margin:auto; padding:44px 32px 64px; }}
h1 {{ font-size:clamp(2rem,5vw,4.6rem); letter-spacing:-.055em; margin:0 0 8px; }}
.subtitle {{ color:var(--muted); margin:0 0 28px; }}
.metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin-bottom:24px; }}
.metric,.panel {{ background:white; border:1px solid #e2e8f0; border-radius:18px; box-shadow:0 12px 35px rgba(15,23,42,.06); }}
.metric {{ padding:20px; }} .metric b {{ display:block; font-size:1.55rem; margin-top:7px; }}
.metric span {{ color:var(--muted); font-size:.82rem; text-transform:uppercase; letter-spacing:.08em; }}
.panel {{ padding:22px; overflow:auto; margin-top:18px; }}
svg {{ min-width:1050px; width:100%; height:auto; }}
.node-label {{ fill:#334155; font-size:12px; }}
.category-label {{ fill:#0f172a; font-size:13px; font-weight:700; text-decoration:underline; cursor:pointer; }}
.root-label {{ fill:#0f172a; font-size:13px; font-weight:800; }}
path {{ transition:fill-opacity .16s ease; }} path:hover {{ fill-opacity:.68; }}
.category-flow {{ cursor:pointer; }} .category-flow:focus {{ outline:3px solid #2563eb; outline-offset:3px; }}
table {{ width:100%; border-collapse:collapse; }} th,td {{ text-align:left; border-bottom:1px solid #e2e8f0; padding:11px 8px; }}
.table-wrap {{ overflow:auto; }}
.category-detail {{ border-top:1px solid #e2e8f0; }}
.category-detail:first-of-type {{ border-top:0; }}
.category-detail summary {{ display:flex; justify-content:space-between; gap:20px; padding:16px 4px; cursor:pointer; font-size:1.05rem; }}
.category-detail summary:hover {{ color:#2563eb; }}
.category-detail[open] summary {{ color:#2563eb; }}
.category-detail table {{ min-width:1050px; margin-bottom:18px; font-size:.87rem; }}
th {{ color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }}
footer {{ color:var(--muted); font-size:.8rem; margin-top:18px; }}
.empty {{ padding:80px; text-align:center; color:var(--muted); }}
</style>
</head>
<body><main>
<h1>Así fluye tu dinero</h1>
<p class="subtitle">{summary['period_start']} → {summary['period_end']} · generado localmente</p>
<section class="metrics">
<div class="metric"><span>Gasto incluido</span><b>{html.escape(_money(total, currency))}</b></div>
<div class="metric"><span>Ingresos observados</span><b>{html.escape(_money(income, currency))}</b></div>
<div class="metric"><span>Balance neto</span><b>{html.escape(_money(net, currency))}</b></div>
<div class="metric"><span>Por revisar</span><b>{summary['uncertain_count']} movimientos</b></div>
</section>
<section class="panel"><h2>Del gasto total al detalle</h2>{sankey}</section>
<section class="panel"><h2>Resumen por categoría</h2>
<table><thead><tr><th>Categoría</th><th>Importe</th><th>Participación</th></tr></thead>
<tbody>{''.join(category_rows)}</tbody></table></section>
<section class="panel" id="transaction-audit"><h2>Transacciones auditables</h2>
<p class="subtitle">Haz clic en una categoría para ver todos los movimientos que forman su total. Los reembolsos aparecen como impacto negativo.</p>
{transaction_details}</section>
<footer>Los pagos de tarjeta y transferencias internas identificados no cuentan como consumo. Generado {generated}.</footer>
<script>
function openCategory(selector) {{
  const target = document.querySelector(selector);
  if (!target) return;
  target.open = true;
  history.replaceState(null, '', selector);
  target.scrollIntoView({{behavior:'smooth', block:'start'}});
}}
function openLinkedCategory() {{
  if (location.hash.startsWith('#category-')) openCategory(location.hash);
}}
document.querySelectorAll('[data-category-target]').forEach((element) => {{
  element.addEventListener('click', () => openCategory(element.dataset.categoryTarget));
  element.addEventListener('keydown', (event) => {{
    if (event.key === 'Enter' || event.key === ' ') {{
      event.preventDefault();
      openCategory(element.dataset.categoryTarget);
    }}
  }});
}});
window.addEventListener('hashchange', openLinkedCategory);
window.addEventListener('DOMContentLoaded', openLinkedCategory);
</script>
</main></body></html>"""


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a standalone spending report from normalized transactions."
    )
    parser.add_argument("input_csv", type=pathlib.Path)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--currency", default="EUR")
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> None:
    """Runs the report generator."""
    options = _parse_args(args)
    rows = _read_transactions(options.input_csv)
    summary = _aggregate(rows)
    options.output_dir.mkdir(parents=True, exist_ok=True)

    json_summary = {
        key: ({f"{item[0]} > {item[1]}": value for item, value in content.items()}
              if key in {"subcategories", "merchants"} and isinstance(content, dict)
              else content)
        for key, content in summary.items()
    }
    (options.output_dir / "finance_summary.json").write_text(
        json.dumps(json_summary, ensure_ascii=False, indent=2, default=_json_decimal) + "\n",
        encoding="utf-8",
    )
    (options.output_dir / "finance_report.md").write_text(
        _build_markdown(summary, options.currency), encoding="utf-8"
    )
    (options.output_dir / "finance_sankey.html").write_text(
        _build_html(summary, options.currency, rows), encoding="utf-8"
    )

    print(f"Created {options.output_dir / 'finance_sankey.html'}")
    print(f"Created {options.output_dir / 'finance_report.md'}")
    print(f"Created {options.output_dir / 'finance_summary.json'}")


if __name__ == "__main__":
    main()
