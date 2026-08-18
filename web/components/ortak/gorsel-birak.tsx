"use client";

import { useCallback, useId, useRef, useState } from "react";
import { ImageUp, X } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { dataUrlOku, gorselDogrula } from "@/lib/dosya";
import { Button } from "@/components/ui/button";

interface Ozellikler {
  deger: string | null;
  onDegisim: (dataUrl: string | null, dosyaAdi: string) => void;
  etiket: string;
  ipucu?: string;
  /** Önizleme kutusunun en-boy oranı; çıktıdaki kutuyla aynı olmalı. */
  oran?: number;
  yukseklikSinifi?: string;
}

export function GorselBirak({
  deger,
  onDegisim,
  etiket,
  ipucu,
  oran,
  yukseklikSinifi = "h-28",
}: Ozellikler) {
  const [uzerinde, setUzerinde] = useState(false);
  const [ad, setAd] = useState("");
  const girdiRef = useRef<HTMLInputElement>(null);
  const girdiId = useId();

  const al = useCallback(
    async (dosya: File | undefined) => {
      if (!dosya) return;
      const hata = gorselDogrula(dosya);
      if (hata) {
        toast.error(hata);
        return;
      }
      try {
        const dataUrl = await dataUrlOku(dosya);
        setAd(dosya.name);
        onDegisim(dataUrl, dosya.name);
      } catch {
        toast.error("Görsel okunamadı, tekrar deneyin.");
      }
    },
    [onDegisim],
  );

  const temizle = () => {
    setAd("");
    onDegisim(null, "");
    if (girdiRef.current) girdiRef.current.value = "";
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <label
          htmlFor={girdiId}
          className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
        >
          {etiket}
        </label>
        {deger && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs text-destructive hover:text-destructive"
            onClick={temizle}
          >
            <X className="size-3" /> Kaldır
          </Button>
        )}
      </div>

      <div
        onDragEnter={(e) => { e.preventDefault(); setUzerinde(true); }}
        onDragOver={(e) => { e.preventDefault(); setUzerinde(true); }}
        onDragLeave={(e) => { e.preventDefault(); setUzerinde(false); }}
        onDrop={(e) => {
          e.preventDefault();
          setUzerinde(false);
          void al(e.dataTransfer.files?.[0]);
        }}
        /* flex + overflow-hidden ZORUNLU: `grid place-items-center` ile satır
           izi içeriğe göre büyür, bu yüzden görselin `max-h-full` sınırı
           çözümlenemez ve büyük bir fotoğraf kutuyu aşıp sayfayı kaplar.
           Flex kapsayıcıda yükseklik kesindir, yüzde sınır çalışır. */
        className={cn(
          "relative flex items-center justify-center overflow-hidden",
          "rounded-md border-2 border-dashed",
          "bg-card/60 transition-colors duration-200",
          uzerinde ? "border-primary bg-primary/5" : "border-input hover:border-primary/60",
          yukseklikSinifi,
        )}
        style={oran ? { aspectRatio: String(oran) } : undefined}
      >
        <input
          id={girdiId}
          ref={girdiRef}
          type="file"
          accept=".png,.jpg,.jpeg,.svg"
          className="absolute inset-0 cursor-pointer opacity-0"
          onChange={(e) => void al(e.target.files?.[0])}
          aria-label={etiket}
        />
        {deger ? (
          /* Kullanıcının yerel data URL'i; next/image optimizasyonu gereksiz. */
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={deger}
            alt={`${etiket} önizlemesi`}
            className="max-h-full max-w-full object-contain p-1"
          />
        ) : (
          <div className="pointer-events-none flex flex-col items-center gap-1 px-3 text-center">
            <ImageUp className="size-5 text-muted-foreground" aria-hidden />
            <span className="text-xs text-muted-foreground">
              Seçmek için tıklayın veya sürükleyin
            </span>
          </div>
        )}
      </div>

      {(ad || ipucu) && (
        <p className="text-[11px] leading-snug text-muted-foreground">
          {ad ? <span className="font-medium text-foreground">{ad}</span> : null}
          {ad && ipucu ? " · " : null}
          {ipucu}
        </p>
      )}
    </div>
  );
}
