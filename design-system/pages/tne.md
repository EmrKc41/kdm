# Tek Nokta Eğitimi Sekmesi

> **Overrides MASTER.md** for the TNE tab only.

## Layout

- **Pattern:** Data-Dense Dashboard — single scroll form with grouped sections
- **Max width:** 1600px centered

## Form Structure

1. **Başlık & birim bilgileri** — compact header block
2. **Eğitim içeriği / türü** — checkbox grid mirroring Excel drawing checkboxes
3. **Eğitim görseli** — large drop zone (maps to B11:G42)
4. **Katılımcı tablosu** — editable rows, max 32, imza column intentionally empty

## Excel Preview Colors (fixed)

| Element | Color | Usage |
|---------|-------|-------|
| Checked checkbox fill | `#00B050` | `--excel-yesil` |
| Unchecked | white + black border | template default |

## Typography Note

- Output title: 24pt (overrides template 36pt — intentional, tested)
- Form labels: 11px uppercase section headers via `Bolum`

## Primary Action

Same sticky `EylemCubugu` as Talimat — amber generate button.

## Accessibility

- Checkbox groups: `fieldset` + `legend` per category (içerik / tür)
- Table: row add/remove buttons with `aria-label`
- Participant count shown in action bar status text

## Anti-Patterns

- Do NOT fill checkbox borders when marking checked — fill only `<a:ln>` preceding region
- Do NOT resize TNE logo to Talimat dimensions — template-specific EMU sizes differ
