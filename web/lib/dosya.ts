export const MAKS_GORSEL_MB = 20;
const KABUL = [".png", ".jpg", ".jpeg", ".svg"];

export function gorselDogrula(dosya: File): string | null {
  const uzanti = dosya.name.slice(dosya.name.lastIndexOf(".")).toLowerCase();
  if (!KABUL.includes(uzanti)) {
    return `"${dosya.name}" desteklenmiyor. Kabul edilenler: ${KABUL.join(", ")}`;
  }
  if (dosya.size > MAKS_GORSEL_MB * 1024 * 1024) {
    return `"${dosya.name}" çok büyük. En fazla ${MAKS_GORSEL_MB} MB olabilir.`;
  }
  if (dosya.size === 0) return `"${dosya.name}" boş görünüyor.`;
  return null;
}

export function dataUrlOku(dosya: File): Promise<string> {
  return new Promise((coz, hata) => {
    const okuyucu = new FileReader();
    okuyucu.onload = () => coz(String(okuyucu.result));
    okuyucu.onerror = () => hata(new Error("Dosya okunamadı."));
    okuyucu.readAsDataURL(dosya);
  });
}

export function yeniId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `id-${Math.random().toString(36).slice(2)}`;
}
