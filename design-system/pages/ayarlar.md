# Ayarlar Sekmesi

> **Overrides MASTER.md** for the Settings tab only.

## Layout

- **Pattern:** Simple settings panel — single column, max-width 640px
- Lower visual density than form tabs

## Content

1. **Normal ünvan listesi** — tag/chip input for titles that render black in vardiya output
2. Future: full rule engine editor (5 operators) — not yet implemented

## Interaction

- Save persists to `ayarlar/kurallar.json` via `POST /api/ayarlar/unvanlar`
- Empty list rejected with clear error (all rows would turn red)
- Success toast confirms save

## Visual Style

- Uses default card + input components
- No Excel preview colors on this page
- Secondary buttons for add/remove title entries

## Accessibility

- List items removable via keyboard-accessible buttons
- Validation error before API call when list empty

## Roadmap (P1)

- Expose `listede`, `esittir`, `icerir`, `bos` operators in UI
- Field targeting (which column the rule applies to)
- Preview table showing rule effect on sample rows
