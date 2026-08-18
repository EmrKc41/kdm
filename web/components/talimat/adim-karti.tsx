"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ChevronDown, ChevronUp, Eraser, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { SARI_ALAN_SINIRI, type KontrolAdimi } from "@/lib/types";
import { Alan } from "@/components/ortak/alan";
import { GorselBirak } from "@/components/ortak/gorsel-birak";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SariOnizleme } from "./sari-onizleme";

interface Ozellikler {
  adim: KontrolAdimi;
  sira: number;                       // görünen numara (1..9)
  toplam: number;
  onDegisim: (yama: Partial<KontrolAdimi>) => void;
  onTemizle: () => void;
  onTasi: (yon: -1 | 1) => void;
}

export function AdimKarti({
  adim, sira, toplam, onDegisim, onTemizle, onTasi,
}: Ozellikler) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: adim.id });

  const uzunluk = adim.baslik.trim().length + adim.aciklama.trim().length;
  const asiyor = uzunluk > SARI_ALAN_SINIRI;
  const dolu = Boolean(
    adim.baslik.trim() || adim.aciklama.trim() || adim.cycle_sn.trim() || adim.gorsel,
  );

  return (
    <article
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        "flex flex-col rounded-lg border bg-card transition-colors duration-200",
        dolu ? "border-primary/50" : "border-border",
        isDragging && "opacity-40 shadow-lg",
      )}
      aria-label={`${sira}. kontrol adımı`}
    >
      <header className="flex items-center gap-2 rounded-t-lg border-b border-border bg-muted/60 px-2 py-1.5">
        {/* Sürükleme tutamağı: klavye ile de çalışır (dnd-kit KeyboardSensor) */}
        <button
          type="button"
          className="rounded p-1 text-muted-foreground hover:bg-background hover:text-foreground cursor-grab active:cursor-grabbing"
          aria-label={`${sira}. adımı taşı — boşluk tuşuyla tut, ok tuşlarıyla taşı`}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" aria-hidden />
        </button>

        {/* Sürükleme tek taşıma yolu olamaz (WCAG 2.2 — Dragging Movements):
            ince motor kontrolü zor olan işaretçi kullanıcısı için düğme şart. */}
        <div className="flex">
          <button
            type="button"
            onClick={() => onTasi(-1)}
            disabled={sira === 1}
            aria-label={`${sira}. adımı yukarı taşı`}
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-background hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
          >
            <ChevronUp className="size-3.5" aria-hidden />
          </button>
          <button
            type="button"
            onClick={() => onTasi(1)}
            disabled={sira === toplam}
            aria-label={`${sira}. adımı aşağı taşı`}
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-background hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
          >
            <ChevronDown className="size-3.5" aria-hidden />
          </button>
        </div>

        <span className="font-mono text-xs font-bold tracking-tight text-primary">
          {sira}. KONTROL ADIMI
        </span>

        {dolu && (
          <span
            className="ml-1 size-1.5 rounded-full bg-primary"
            aria-label="dolu"
          />
        )}

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onTemizle}
          disabled={!dolu}
          className="ml-auto h-6 px-2 text-xs text-destructive hover:text-destructive disabled:opacity-40"
        >
          <Eraser className="size-3" /> Temizle
        </Button>
      </header>

      <div className="flex flex-col gap-3 p-3">
        <GorselBirak
          deger={adim.gorsel}
          onDegisim={(gorsel, gorselAdi) => onDegisim({ gorsel, gorselAdi })}
          etiket="Adım Fotoğrafı"
          ipucu="Çıktıda tam 5 × 17 cm, metin kutularının arkasında"
          yukseklikSinifi="h-24"
        />

        <Alan etiket="Cycle Süresi (saniye)" htmlFor={`cycle-${adim.id}`}>
          <Input
            id={`cycle-${adim.id}`}
            type="number"
            min={0}
            inputMode="numeric"
            placeholder="3"
            value={adim.cycle_sn}
            onChange={(e) => onDegisim({ cycle_sn: e.target.value })}
            className="font-mono"
          />
        </Alan>

        <Alan etiket="Sarı Alan Başlığı" htmlFor={`baslik-${adim.id}`}>
          <Input
            id={`baslik-${adim.id}`}
            value={adim.baslik}
            onChange={(e) => onDegisim({ baslik: e.target.value })}
            placeholder="MARKALAMA"
          />
        </Alan>

        <Alan etiket="Sarı Alan Açıklaması" htmlFor={`aciklama-${adim.id}`}>
          <Textarea
            id={`aciklama-${adim.id}`}
            rows={3}
            value={adim.aciklama}
            onChange={(e) => onDegisim({ aciklama: e.target.value })}
            placeholder="BELİRTİLEN BÖLGEDE PARÇANIN ÜST KISMINDA..."
            aria-describedby={`sayac-${adim.id}`}
            aria-invalid={asiyor}
          />
          <p
            id={`sayac-${adim.id}`}
            className={cn(
              "text-right font-mono text-[11px] tabular-nums",
              asiyor ? "font-bold text-destructive" : "text-muted-foreground",
            )}
            aria-live="polite"
          >
            {uzunluk} / {SARI_ALAN_SINIRI}
            {asiyor && " — sığmıyor"}
          </p>
        </Alan>

        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Çıktı Önizlemesi
          </span>
          <SariOnizleme baslik={adim.baslik} aciklama={adim.aciklama} />
        </div>
      </div>
    </article>
  );
}
