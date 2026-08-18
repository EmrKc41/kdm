# Kalite Raporu Sekmesi

> **Overrides MASTER.md** for the Rapor tab only.

## Layout

- **Pattern:** Data-Dense Dashboard — meta grid + summary + editable table
- **Max width:** 1600px, table horizontally scrollable

## Form Structure

1. **Rapor kimliği** — başlık, konu*, rapor no, tarih, hazırlayan, genel durum
2. **Özet** — textarea (maps to Excel merged cell)
3. **Uygunsuzluk satırları** — inline table (7 columns)

## Primary Action

Same sticky `EylemCubugu` — amber generate button, `tip: rapor`.

## Validation

- Konu zorunlu (client + server)
- Başlık veya konu en az biri (server fallback)

## Excel Output

- A4 portrait, corporate blue header band
- Frozen table header row
- Alternating row shading
