/** ISO (YYYY-AA-GG) -> Türkçe (GG.AA.YYYY). Boş girdi boş döner. */
export function ggaayyyy(iso: string): string {
  if (!iso) return "";
  const [y, a, g] = iso.split("-");
  return y && a && g ? `${g}.${a}.${y}` : "";
}

/** Türkçe (GG.AA.YYYY) -> ISO (YYYY-AA-GG). */
export function isoya(tr: string): string {
  if (!tr?.includes(".")) return "";
  const [g, a, y] = tr.split(".");
  return y && a && g ? `${y}-${a}-${g}` : "";
}

export function bugun(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const AYLAR = [
  "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
];

/** core/tarih.py ile aynı kural: 17 Ağustos -> "Ağustos3.Hafta". */
export function haftaAdi(iso: string): string {
  const d = iso ? new Date(iso) : new Date();
  if (Number.isNaN(d.getTime())) return "";
  return `${AYLAR[d.getMonth()]}${Math.floor((d.getDate() - 1) / 7) + 1}.Hafta`;
}
