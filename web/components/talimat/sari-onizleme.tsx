import { cn } from "@/lib/utils";

interface Ozellikler {
  baslik: string;
  aciklama: string;
  className?: string;
}

/**
 * Sarı açıklama alanının BİREBİR aynası.
 *
 * Çıktıdaki hücre: dolgu FFFF00, başlık kırmızı + kalın, açıklama siyah +
 * kalın, ikisi de 14 punto ve alt alta. Buradaki renkler doğrudan Excel
 * değerleridir (--excel-*), tema renkleri değil — karanlık modda da kağıttaki
 * görüntü aynı kalmalı.
 */
export function SariOnizleme({ baslik, aciklama, className }: Ozellikler) {
  const bos = !baslik.trim() && !aciklama.trim();

  return (
    <div
      className={cn(
        "min-h-16 rounded-sm border px-2.5 py-2 text-[13px] leading-snug",
        "font-bold whitespace-pre-wrap break-words",
        className,
      )}
      style={{
        backgroundColor: "var(--excel-sari)",
        borderColor: "var(--excel-sari-kenar)",
      }}
    >
      {bos ? (
        <span className="font-normal italic text-black/45">
          Başlık ve açıklama girdikçe çıktıdaki görünüm burada belirir.
        </span>
      ) : (
        <>
          {baslik.trim() && (
            <span style={{ color: "var(--excel-kirmizi)" }}>{baslik.trim()}</span>
          )}
          {baslik.trim() && aciklama.trim() && "\n"}
          {aciklama.trim() && <span className="text-black">{aciklama.trim()}</span>}
        </>
      )}
    </div>
  );
}
