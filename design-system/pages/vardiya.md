# Vardiya Listesi Sekmesi

> **Overrides MASTER.md** for the Vardiya tab only.

## Layout

- **Pattern:** Data-Dense Dashboard — tabbed shift selector + editable data table
- **Max width:** 1600px, table horizontally scrollable on narrow screens

## Form Structure

1. **Hafta tarihi** — date picker, drives output filename
2. **Vardiya sekmeleri** — A / B / C with preset hours from API
3. **Personel tablosu** — inline edit, import button, row highlighting for rule violations
4. **Import dialog** — CSV/Excel drop zone

## Data Visualization

- Rows where `ünvan ∉ normal_unvanlar` → red bold (matches Excel output)
- Phone column: monospace tabular nums (`font-mono`)
- No chart widgets — pure table focus

## Primary Action

- Generate produces **all three shifts** on one sheet (not just active tab)
- Project file stores all shifts + title rules

## Accessibility

- Table headers sticky within scroll container
- Import errors as toast with column name hint
- Coarse pointer: 44px min row input height (globals.css)

## Anti-Patterns

- Do NOT silently drop leading zeros on phone — text format enforced server-side
- Do NOT filter out red rows — they are intentional QA signal
