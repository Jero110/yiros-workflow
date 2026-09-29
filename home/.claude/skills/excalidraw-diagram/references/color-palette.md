# Color Palette & Brand Style

**This is the single source of truth for all colors and brand-specific styles.** To customize diagrams for your own brand, edit this file — everything else in the skill is universal.

---

## Dark Mode Theme

Canvas background: `#0f1117`

---

## Shape Colors (Semantic)

Colors encode meaning, not decoration. Each semantic purpose has a fill/stroke pair.

| Semantic Purpose | Fill | Stroke |
|------------------|------|--------|
| Primary/Neutral | `#1e3a5f` | `#3b82f6` |
| Secondary | `#1e2d4a` | `#60a5fa` |
| Tertiary | `#172035` | `#93c5fd` |
| Start/Trigger | `#431407` | `#f97316` |
| End/Success | `#052e16` | `#22c55e` |
| Warning/Reset | `#450a0a` | `#f87171` |
| Decision | `#422006` | `#f59e0b` |
| AI/LLM | `#2e1065` | `#a78bfa` |
| Inactive/Disabled | `#1e2d4a` | `#60a5fa` (use dashed stroke) |
| Error | `#450a0a` | `#ef4444` |
| Surface/Panel | `#161b27` | `#2d3748` |
| Deep Surface | `#0d1117` | `#1e2d4a` |

**Rule**: Dark fill + bright/saturated stroke for contrast on dark background.

---

## Text Colors (Hierarchy)

Use color on free-floating text to create visual hierarchy without containers.

| Level | Color | Use For |
|-------|-------|---------|
| Title | `#e2e8f0` | Section headings, major labels |
| Subtitle | `#93c5fd` | Subheadings, secondary labels |
| Body/Detail | `#64748b` | Descriptions, annotations, metadata |
| Accent | `#a78bfa` | Highlights, AI-related labels |
| On dark fills | `#e2e8f0` | Text inside shapes |
| Muted | `#475569` | Timestamps, minor metadata |

---

## Evidence Artifact Colors

Used for code snippets, data examples, and other concrete evidence inside technical diagrams.

| Artifact | Background | Text Color |
|----------|-----------|------------|
| Code snippet | `#0d1117` | `#7dd3fc` (blue) |
| JSON/data example | `#0d1117` | `#4ade80` (green) |
| Cost label | `#0d1117` | `#fbbf24` (amber) |

---

## Default Stroke & Line Colors

| Element | Color |
|---------|-------|
| Arrows | Use the stroke color of the source element's semantic purpose |
| Structural lines (dividers, trees, timelines) | `#2d3748` or `#334155` |
| Marker dots (fill + stroke) | `#3b82f6` |
| Section dividers | `#1e2d4a` |

---

## Background

| Property | Value |
|----------|-------|
| Canvas background | `#0f1117` |
