---
name: finance-sankey
description: Analiza uno o varios estados de cuenta bancarios o de tarjeta, clasifica cada movimiento con detalle, detecta suscripciones y transferencias, evita dobles conteos y crea un informe privado de gastos con un diagrama Sankey. Úsala siempre que el usuario entregue extractos PDF/CSV/XLSX, movimientos bancarios o exportaciones de tarjetas y quiera saber en qué gasta, cuánto se va en comida, suscripciones u otras categorías, comparar periodos o visualizar el flujo del dinero.
compatibility: Requiere Python 3 estándar. Para leer PDF o Excel, usa además las herramientas/skills disponibles para esos formatos.
---

# Finance Sankey

Convierte estados de cuenta en un análisis auditable: cada cifra del resumen debe poder rastrearse hasta movimientos concretos. Prioriza exactitud y privacidad sobre una clasificación aparentemente completa.

## Privacidad

- Procesa los archivos localmente.
- No envíes transacciones, nombres, direcciones, números de cuenta o comercios a servicios web sin permiso explícito.
- No expongas números completos de cuenta o tarjeta en los entregables. Conserva como máximo los últimos cuatro dígitos cuando sean necesarios para distinguir cuentas.
- Guarda los resultados junto a los archivos de trabajo o en la ubicación solicitada por el usuario; no sustituyas los originales.

## Entradas admitidas

Acepta uno o varios PDF, CSV, TSV o XLSX de bancos y tarjetas. Si el formato requiere otra skill (PDF o xlsx), cárgala y úsala para extraer las tablas; esta skill gobierna la normalización, clasificación, conciliación y presentación financiera.

Si falta un dato indispensable, pregunta solo lo necesario. Normalmente basta con confirmar:

1. moneda cuando no sea evidente;
2. si los cargos aparecen positivos o negativos;
3. periodo deseado cuando los archivos abarcan fechas diferentes.

## Flujo de trabajo

### 1. Inventariar y extraer

- Registra cada archivo, cuenta, moneda, rango de fechas y saldo inicial/final disponible.
- Extrae fecha, descripción, importe, cuenta y cualquier tipo de movimiento ofrecido por el banco.
- Si un PDF es escaneado, aplica OCR y revisa visualmente una muestra; no confíes en OCR silenciosamente.
- Conserva el texto original de cada descripción para auditoría.

### 2. Normalizar

Crea `transactions_normalized.csv` en UTF-8 con estas columnas, en este orden:

```csv
date,description,amount,currency,account,merchant,category,subcategory,transaction_type,confidence,notes,source_file
```

Reglas:

- Usa fecha ISO `YYYY-MM-DD`.
- Convierte gastos a importes negativos e ingresos/reembolsos a positivos.
- Usa `transaction_type`: `expense`, `income`, `refund`, `transfer`, `card_payment`, `fee` o `unknown`.
- Normaliza el comercio sin borrar `description` (por ejemplo, varias variantes de `NETFLIX.COM` → `Netflix`).
- Usa `confidence`: `high`, `medium` o `low`.
- No inventes la identidad o finalidad de un comercio ambiguo. Marca `low` y explica la duda en `notes`.
- Conserva una fila por movimiento; no agregues antes de conciliar.

### 3. Conciliar y evitar dobles conteos

Esta etapa es obligatoria cuando hay varias cuentas o tarjetas.

- Detecta duplicados por fecha aproximada, importe, descripción y cuenta; no elimines coincidencias solo por compartir importe.
- Empareja transferencias internas: mismo importe absoluto, signos opuestos, fechas cercanas y cuentas propias distintas.
- Marca el pago de una tarjeta como `card_payment` si también están presentes las compras de esa tarjeta. Exclúyelo del gasto para no contar dos veces.
- Mantén transferencias, pagos de tarjeta y duplicados identificados en el CSV, pero fuera del total de consumo.
- Trata retiros de efectivo como `Efectivo / Retiro sin desglose`, salvo que el usuario aporte el destino real.
- Netea un reembolso contra la categoría original cuando el vínculo sea razonablemente claro. Si no lo es, déjalo como `refund` y explícalo.
- Si hay saldos, comprueba la conciliación: saldo inicial + entradas + salidas ≈ saldo final. Explica diferencias por movimientos pendientes, fechas de corte o extracción incompleta.

### 4. Clasificar con detalle

Usa `references/taxonomy.md` como base y consulta `references/merchant-rules.md` antes de clasificar. Las reglas de comercios confirmadas por el usuario tienen prioridad cuando el descriptor coincide; sus límites evitan extender una regla a comercios parecidos. Clasifica primero por evidencia del descriptor y patrones repetidos, no por suposición genérica.

- Separa categoría y subcategoría: `Alimentación > Restaurantes`, no solo `Comida`.
- Reutiliza las reglas confirmadas en `references/merchant-rules.md` en estados futuros. Si el usuario corrige otra clasificación recurrente, añade una regla precisa con patrón, categoría, subcategoría, confianza y excepción.
- Detecta suscripciones por recurrencia, descriptor conocido o cobro periódico. No etiquetes una compra aislada como suscripción solo por ser digital.
- En `Suscripciones`, conserva subcategorías útiles y el comercio: streaming, software, almacenamiento, noticias, membresías, etc.
- Señala posibles suscripciones olvidadas, aumentos de precio y servicios duplicados, pero formula estas señales como hallazgos, no como hechos cuando la evidencia sea débil.
- Si más del 5 % del gasto queda con confianza baja o sin clasificar, incluye una tabla de revisión y pide aclaraciones antes de presentar conclusiones tajantes.

### 5. Validar

Antes de crear el informe:

- Comprueba que la suma de categorías coincide con el total de gastos incluidos.
- Comprueba que las transacciones excluidas tienen motivo (`transfer`, `card_payment` o duplicado documentado).
- Busca fechas/importes imposibles, monedas mezcladas y signos inconsistentes.
- Resume el número de movimientos incluidos, excluidos y dudosos.

### 6. Generar los entregables

Ejecuta:

```bash
python3 <skill-dir>/scripts/build_finance_report.py \
  transactions_normalized.csv \
  --output-dir <directorio-salida> \
  --currency EUR
```

Sustituye `<skill-dir>` por el directorio de esta skill y la moneda según corresponda. El script crea:

- `finance_sankey.html`: diagrama Sankey autónomo y privado, sin dependencias externas; las bandas, nodos y nombres de categoría son pulsables y abren todas las transacciones, descripciones originales, cuentas, importes, confianza y notas que forman el total;
- `finance_report.md`: resumen cuantitativo;
- `finance_summary.json`: agregados reutilizables.

Completa `finance_report.md` con observaciones cualitativas que los agregados no capturen.

## Estructura del informe final

Mantén este orden:

1. **Resumen ejecutivo**: gasto total, ingresos observados, balance neto, periodo y cuentas.
2. **A dónde se fue el dinero**: categorías con importe, porcentaje y variación si hay varios periodos.
3. **Detalle por subcategoría y comercio**: principales responsables de cada categoría.
4. **Suscripciones**: comercio, importe, frecuencia estimada, coste mensual y anualizado; separa confirmadas de posibles.
5. **Hallazgos**: concentraciones de gasto, comisiones, aumentos, duplicidades o anomalías.
6. **Movimientos excluidos**: transferencias internas, pagos de tarjeta y duplicados, con sus totales.
7. **Por revisar**: transacciones ambiguas y preguntas concretas.
8. **Metodología y límites**: reglas de signos, cobertura, conciliación y cualquier OCR o dato faltante.

No des asesoramiento financiero categórico ni juzgues los hábitos. Describe patrones verificables y, si el usuario lo pide, ofrece oportunidades de ahorro con supuestos explícitos.

## Entrega al usuario

Indica claramente las rutas de los cuatro archivos: CSV normalizado, HTML Sankey, informe Markdown y resumen JSON. Da un resumen breve en el chat y menciona cualquier incertidumbre material.