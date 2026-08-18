"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type Durum = "bilinmiyor" | "acik" | "kapali" | "sablon_eksik";

const METIN: Record<Durum, string> = {
  bilinmiyor: "Motor durumu kontrol ediliyor…",
  acik: "Excel motoru çalışıyor · şablonlar hazır",
  sablon_eksik: "Motor çalışıyor ancak şablon dosyaları eksik (templates/)",
  kapali:
    "Excel motoruna ulaşılamıyor. Başlatmak için: python calistir.py",
};

export function MotorDurumu() {
  const [durum, setDurum] = useState<Durum>("bilinmiyor");

  useEffect(() => {
    let iptal = false;

    const yokla = async () => {
      try {
        const yanit = await fetch("/api/health", { cache: "no-store" });
        if (!iptal) {
          if (!yanit.ok) {
            setDurum("kapali");
            return;
          }
          const govde = (await yanit.json()) as {
            durum?: string;
            tum_sablonlar_hazir?: boolean;
          };
          if (govde.durum !== "acik") {
            setDurum("kapali");
          } else if (govde.tum_sablonlar_hazir === false) {
            setDurum("sablon_eksik");
          } else {
            setDurum("acik");
          }
        }
      } catch {
        if (!iptal) setDurum("kapali");
      }
    };

    void yokla();
    const zaman = setInterval(yokla, 30_000);
    return () => {
      iptal = true;
      clearInterval(zaman);
    };
  }, []);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className="flex items-center gap-1.5 rounded-md border border-border px-2 py-1"
          role="status"
          aria-label={METIN[durum]}
        >
          <span
            className={cn(
              "size-1.5 rounded-full transition-colors duration-300",
              durum === "acik" && "bg-[var(--excel-yesil)]",
              durum === "sablon_eksik" && "bg-accent",
              durum === "kapali" && "bg-destructive",
              durum === "bilinmiyor" && "animate-pulse bg-muted-foreground/50",
            )}
            aria-hidden
          />
          <span className="hidden text-[11px] font-medium text-muted-foreground sm:inline">
            Motor
          </span>
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-64">{METIN[durum]}</TooltipContent>
    </Tooltip>
  );
}
