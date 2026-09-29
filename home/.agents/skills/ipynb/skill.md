---
name: ipynb
description: Expert in working with Jupyter notebooks (.ipynb files). Use this skill when the user needs to create, edit, debug, or improve Jupyter notebooks, especially for R/Python statistical analysis, data visualization, or academic assignments. Handles UTF-8 encoding issues, creates professional plots, and ensures clean notebook structure.
---

This skill provides comprehensive guidance for working with Jupyter notebooks (.ipynb files), particularly for statistical computing with R, data visualization, and academic work.

## Core Principles

1. **Always use NotebookEdit tool** - Never manually edit JSON
2. **UTF-8 Safety** - Avoid accented characters in R output (use ASCII)
3. **Professional Plots** - Clean, simple, publication-quality visualizations
4. **Proper Cell Order** - Logical flow from markdown → code → output
5. **LaTeX Correctness** - Proper math mode delimiters and escaping

## Working with Notebooks

### Reading Notebooks

Use the Read tool to view notebook contents:
```
Read tool: /path/to/notebook.ipynb
```

Notebooks display as:
```
<cell id="cell-0"><cell_type>markdown</cell_type>
# Title
Content here
</cell>

<cell id="cell-1"><language>R</language>
# R code here
x <- 1:10
</cell>
```

### Editing Cells

Use NotebookEdit to modify cells:

**Replace cell content:**
```
NotebookEdit:
  notebook_path: /path/to/notebook.ipynb
  cell_id: cell-5
  new_source: |
    # Updated R code
    plot(x, y)
```

**Insert new cell:**
```
NotebookEdit:
  notebook_path: /path/to/notebook.ipynb
  cell_id: cell-3  # Insert after this cell
  edit_mode: insert
  cell_type: code  # or "markdown"
  new_source: |
    # New code here
```

**Delete cell:**
```
NotebookEdit:
  notebook_path: /path/to/notebook.ipynb
  cell_id: cell-7
  edit_mode: delete
  new_source: ""  # Required but ignored
```

## UTF-8 Encoding Issues

### Problem
R's `cat()` and `knitr::kable()` can produce UTF-8 characters that display as `<U+00F3>` in notebook output.

### Common Issues:
- `ó` → `<U+00F3>`
- `í` → `<U+00ED>`
- `á` → `<U+00E1>`
- `¿` → `<U+00BF>`

### Solution: Use ASCII Characters

**Bad (causes UTF-8 errors):**
```r
cat("Correlación empírica:", rho, "\n")
knitr::kable(df, col.names = c("X₁", "X₂", "ρ̂"))
```

**Good (ASCII safe):**
```r
cat("Correlacion empirica:", rho, "\n")
knitr::kable(df, col.names = c("X1", "X2", "rho_hat"))
```

**For plots, use `expression()` for math symbols:**
```r
plot(x, y,
     xlab = expression(rho[Z]),
     ylab = expression(hat(rho)[X]))
```

## LaTeX in Markdown Cells

### Math Mode Delimiters

**Inline math:** Use single `$`
```markdown
The variance is $\sigma^2$ and mean is $\mu$.
```

**Display math:** Use double `$$` on separate lines
```markdown
$$f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}$$
```

### Common LaTeX Errors

**Error: Extra `$` in equation**
```markdown
# BAD - mixing delimiters
$$c \cdot g(x) \geq f(x)$$ donde $x \in S$
```

**Fixed:**
```markdown
$$c \cdot g(x) \geq f(x) \quad \text{para todo } x \in S$$

donde $S = \{x: f(x) > 0\}$.
```

**Escaping Special Characters:**
- Braces in text: `\{` and `\}`
- Backslash: `\\` (double backslash in JSON strings)

Example in notebook:
```markdown
$$\mathcal{S}_f = \\{x\in\mathbb{R}: f(x)>0 \\}$$
```

## User's Preferred Plot Style

### Style Reference
The user's preferred aesthetic matches a clean matplotlib style:
- **White background, no grid**
- **No top/right border spines** — only bottom + left axes visible
- **Large, readable sans-serif text** — titles ~1.4×, axis labels ~1.2×
- **Single mid-weight line** — `lwd = 2` (not too thin, not too thick)
- **Primary color: `"#4C72B0"`** (matplotlib default blue) for main series
- **No fill** in line plots — pure line only
- **Legends without box**, small, `cex = 0.9`
- **No grid lines** — rely on axis ticks only
- **Ticks pointing inward** (`tcl = -0.4`)

### Global par() Setup (always call at top of each plot block)

```r
par(
  family = "sans",          # Clean sans-serif font (matches matplotlib default)
  cex.main = 1.4,           # Large title
  cex.lab  = 1.2,           # Readable axis labels
  cex.axis = 1.0,           # Readable tick labels
  font.main = 1,            # Title not bold (matches matplotlib default weight)
  bty = "l",                # Only bottom + left axes (no top/right spines)
  las = 1,                  # Horizontal axis labels
  tcl = -0.4,               # Ticks pointing inward
  mgp = c(2.2, 0.6, 0),    # Axis title, tick label, axis line positions
  mar = c(4.5, 4.5, 3.5, 1.5)  # Generous margins
)
```

### Color Palette

```r
# Primary matplotlib-style blue for main series
col_main   <- "#4C72B0"   # matplotlib default blue
col_second <- "#DD8452"   # matplotlib default orange
col_third  <- "#55A868"   # matplotlib default green
col_dark   <- "#2d2d2d"   # near-black for overlaid curves / reference lines
col_fill   <- "#A8C8E8"   # light blue for histogram fill (desaturated)
col_gray   <- "#888888"   # gray for secondary reference lines
```

### Python — Seaborn Palette Setup

For Python plots, use seaborn to set the palette globally. Preferred approach:

```python
import seaborn as sns
sns.reset_defaults()
sns.set_palette('deep', 10)  # default — professional, categorical

# Then read colors from rcParams so they stay in sync with the active palette:
import matplotlib as mpl
_COLORS = [c['color'] for c in mpl.rcParams['axes.prop_cycle']]
```

**Palette options** (change one line to swap):

Categorical (multiple series):
- `"deep"` — default, professional
- `"muted"` — softer tones
- `"colorblind"` — accessible
- `"Set2"`, `"Dark2"`, `"Paired"` — ColorBrewer categorical

Sequential (single series, ordered data):
- `"Blues"`, `"Greens"`, `"Purples"`, `"Oranges"`
- `"YlOrRd"`, `"BuGn"`, `"PuBuGn"`

Diverging (data with a midpoint):
- `"RdBu"`, `"Spectral"`, `"RdYlGn"`, `"PuOr"`

```python
# Examples:
sns.set_palette('muted', 10)
sns.set_palette('colorblind', 10)
sns.set_palette('Set2', 8)
sns.set_palette('Blues', 10)
sns.set_palette('Spectral', 10)
```

### Line Plot Template

```r
par(family="sans", cex.main=1.4, cex.lab=1.2, cex.axis=1.0, font.main=1,
    bty="l", las=1, tcl=-0.4, mgp=c(2.2,0.6,0), mar=c(4.5,4.5,3.5,1.5))

plot(x, y,
     type = "l",
     col  = col_main,
     lwd  = 2,
     xlab = "x label",
     ylab = "y label",
     main = "Descriptive Title")

# Reference line if needed
abline(h = ref_val, lty = 2, col = col_dark, lwd = 1.5)

legend("topright",
       legend = c("Series 1", "Ref"),
       col    = c(col_main, col_dark),
       lwd    = c(2, 1.5), lty = c(1, 2),
       bty    = "n", cex = 0.9)
```

### Histogram Template

```r
par(family="sans", cex.main=1.4, cex.lab=1.2, cex.axis=1.0, font.main=1,
    bty="l", las=1, tcl=-0.4, mgp=c(2.2,0.6,0), mar=c(4.5,4.5,3.5,1.5))

hist(data,
     probability = TRUE,
     breaks = 40,
     main   = "Distribution of X",
     xlab   = "x",
     ylab   = "Density",
     col    = col_fill,
     border = "white")

curve(dnorm(x, mean, sd), add = TRUE, col = col_dark, lwd = 2)

legend("topright",
       legend = c("Data", "Theoretical"),
       col    = c(col_fill, col_dark),
       lwd    = c(8, 2),
       bty    = "n", cex = 0.9)
```

### Barplot Template

```r
par(family="sans", cex.main=1.4, cex.lab=1.2, cex.axis=1.0, font.main=1,
    bty="l", las=1, tcl=-0.4, mgp=c(2.2,0.6,0), mar=c(4.5,4.5,3.5,1.5))

barplot(probs_emp,
        main   = "Title",
        xlab   = "State",
        ylab   = "Proportion",
        col    = col_fill,
        border = "white",
        ylim   = c(0, max(probs_emp) * 1.15))

abline(h = ref, lty = 2, col = col_dark, lwd = 1.5)
legend("topright", legend = "Reference", lty = 2,
       col = col_dark, lwd = 1.5, bty = "n", cex = 0.9)
```

### IMPORTANT: Never combine plots in one figure

**Always put each plot in its own cell.** Never use `par(mfrow=...)` to combine multiple plots. Each chart gets its own `set_style()` call and its own cell.

```r
# WRONG — never do this:
par(mfrow = c(1, 2))
plot(...)  # plot 1
plot(...)  # plot 2

# CORRECT — separate cells:
# Cell 1:
set_style()
plot(...)  # plot 1
legend(...)

# Cell 2:
set_style()
plot(...)  # plot 2
legend(...)
```

### Multi-trajectory Line Plot (Markov chains)

```r
colores_traj <- c("#4C72B0","#DD8452","#55A868","#C44E52","#8172B2")

par(family="sans", cex.main=1.4, cex.lab=1.2, cex.axis=1.0, font.main=1,
    bty="l", las=1, tcl=-0.4, mgp=c(2.2,0.6,0), mar=c(4.5,4.5,3.5,1.5))

plot(NULL, xlim=c(1,n), ylim=c(0,1), xlab="Step n", ylab="Cumulative proportion", main="Title")
for (k in 1:5) lines(traj_k, col=colores_traj[k], lwd=1.8)
abline(h=ref, lty=2, col=col_dark, lwd=1.5)
legend("topright", legend="pi theoretical", lty=2, col=col_dark, lwd=1.5, bty="n", cex=0.9)
```

## Common Plot Mistakes to Avoid

❌ **Don't:**
- Use default R colors (black, red, green, blue named colors)
- Use `col = "lightblue"`, `col = "steelblue"`, `col = "darkgreen"` (named colors)
- Leave `bty = "o"` (default box) — always set `bty = "l"`
- Forget to set `set_style()` before each plot
- Add grid lines — the user's style has NO grid
- Use bold titles — `font.main = 1` (plain)
- Use tiny text — minimum `cex = 0.9`
- Use emojis or unicode in R labels
- **Combine multiple plots in one cell with `par(mfrow=...)` — always separate into individual cells**
- Use multiple colors without a legend — every color must be labeled

✅ **Do:**
- Always call `par(family="sans", ...)` at the start of every plot block
- Use `col_main = "#4C72B0"` as the primary color
- Use `bty = "l"`, `las = 1`, `tcl = -0.4`
- Remove grid — clean white background only
- Use `expression()` for math in axis labels
- Set `border = "white"` on histograms
- Reset `par` after multi-panel plots

## Reorganizing Notebook Cells

If cells are out of order, use Python to reorganize:

```python
import json

with open('notebook.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define correct order by cell indices
correct_order = [0, 1, 2, 5, 6, 3, 4, 7]

# Reorder cells
nb['cells'] = [nb['cells'][i] for i in correct_order]

with open('notebook.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
```

## Tables with knitr::kable

```r
# Create data frame
results <- data.frame(
  Method = c("Method A", "Method B", "Method C"),
  Efficiency = c(0.85, 0.92, 0.78),
  Time_sec = c(1.2, 0.8, 1.5)
)

# Format table (ASCII column names!)
knitr::kable(results,
             digits = 4,
             col.names = c("Method", "Efficiency", "Time (sec)"))
```

**Important:** Use ASCII characters in `col.names` to avoid UTF-8 issues!

## Debugging Notebooks

### Common Issues and Solutions

**Issue: Cell not found**
- Check cell IDs with Read tool first
- Cell IDs may have changed after previous edits

**Issue: KaTeX parse error**
- Check for unmatched `$` or `$$`
- Ensure math mode delimiters are on separate lines for display math
- Escape special characters: `\{`, `\}`, `\\`

**Issue: UTF-8 encoding in output**
- Replace accented characters with ASCII in R code
- Use `expression()` in plots for math symbols
- Avoid unicode subscripts/superscripts in table headers

**Issue: Plot looks unprofessional**
- Apply professional color palette
- Remove borders: `bty = "l"`, `border = "white"`
- Increase line width: `lwd = 2.5`
- Horizontal labels: `las = 1`
- Clean legends: `bty = "n"`

## Best Practices Summary

1. **Always read the notebook first** before making edits
2. **Use NotebookEdit tool** - never manually edit JSON
3. **Test for UTF-8 issues** - use ASCII in R outputs
4. **Professional plots** - use the templates above
5. **Logical cell order** - explanation → code → results
6. **Clean LaTeX** - proper delimiters and escaping
7. **Consistent style** - use same color palette throughout

## Example Workflow

When user asks to "complete and fix my notebook":

1. **Read notebook** to understand structure and find errors
2. **Identify issues:** UTF-8 problems, LaTeX errors, missing code, bad plots
3. **Fix UTF-8:** Replace accented characters in R code
4. **Complete code:** Fill in missing implementations
5. **Improve plots:** Apply professional styling
6. **Check LaTeX:** Fix math mode delimiters
7. **Verify order:** Ensure cells flow logically

Always execute changes incrementally and verify each step works before proceeding.
