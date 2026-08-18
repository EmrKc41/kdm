# İş Talimatı Sekmesi

> **Overrides MASTER.md** for the Talimat tab only.

## Layout

- **Pattern:** Data-Dense Dashboard — multi-column form grid, sticky action bar
- **Max width:** 1600px centered
- **Section spacing:** `--space-md` (16px) between `Bolum` cards

## Form Structure

1. **Başlık & Konu** — two-column on `md+`, stacked on mobile
2. **Logo & İSG** — side by side; ISG selector shows ISO 7010 preview icons
3. **Meta alanları** — 3-column grid (tarih, hazırlayan, rev)
4. **Kontrol adımları** — vertical stack of 9 `AdimKarti` cards with dnd-kit reorder

## Excel Preview Colors (fixed — NOT theme tokens)

| Element | Color | Usage |
|---------|-------|-------|
| Sarı alan zemin | `#FFFF00` | `--excel-sari` |
| Sarı kenarlık | `#D4BD00` | `--excel-sari-kenar` |
| Başlık metni | `#FF0000` | `--excel-kirmizi` |
| Açıklama metni | `#000000` | black, bold |

These colors stay identical in dark mode — they represent paper output.

## Primary Action

- **Excel Dosyası Üret** — amber accent (`--accent`), sticky bottom bar
- Secondary actions: Boş Şablon, Proje Kaydet/Yükle, Temizle — outline variant

## Accessibility

- Step reorder: keyboard via `KeyboardSensor` (Space to pick up, arrows to move)
- Character counter on yellow fields — live `aria-live` on limit warning
- Image upload: drag-drop zone with visible focus ring

## Anti-Patterns for This Page

- Do NOT use emoji for ISG icons — SVG only
- Do NOT hide validation errors until submit — toast + inline where possible
- Do NOT animate card transforms on hover (layout shift)
