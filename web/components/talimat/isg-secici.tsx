"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { isgIkonlariniGetir } from "@/lib/api";
import type { IsgIkon } from "@/lib/types";
import { Skeleton } from "@/components/ortak/iskelet";

interface Ozellikler {
  secilenler: string[];
  onDegisim: (secilenler: string[]) => void;
}

const RAHAT_SIGAN = 5;

export function IsgSecici({ secilenler, onDegisim }: Ozellikler) {
  const [ikonlar, setIkonlar] = useState<IsgIkon[] | null>(null);
  const [hata, setHata] = useState(false);

  useEffect(() => {
    let iptal = false;
    isgIkonlariniGetir()
      .then((v) => !iptal && setIkonlar(v))
      .catch(() => !iptal && setHata(true));
    return () => { iptal = true; };
  }, []);

  const degistir = (ad: string) =>
    onDegisim(
      secilenler.includes(ad)
        ? secilenler.filter((x) => x !== ad)
        : [...secilenler, ad],
    );

  if (hata) {
    return (
      <p className="text-sm text-destructive">
        İkon listesi yüklenemedi. Excel motorunun çalıştığını kontrol edin.
      </p>
    );
  }

  if (!ikonlar) {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 8 }, (_, i) => (
          <Skeleton key={i} className="h-14 rounded-md" />
        ))}
      </div>
    );
  }

  return (
    <>
      <div
        role="group"
        aria-label="İSG ekipmanı seçimi"
        className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4"
      >
        {ikonlar.map(({ ad, etiket }) => {
          const secili = secilenler.includes(ad);
          return (
            <label
              key={ad}
              className={cn(
                "group flex items-center gap-2.5 rounded-md border px-2.5 py-2",
                "transition-all duration-200 hover:border-primary/60",
                "has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring has-[:focus-visible]:ring-offset-1",
                secili
                  ? "border-primary bg-primary/5 shadow-[inset_0_0_0_1px_var(--primary)]"
                  : "border-input bg-card",
              )}
            >
              <input
                type="checkbox"
                name="isg-ikonlari"
                value={ad}
                checked={secili}
                onChange={() => degistir(ad)}
                className="sr-only"
              />
              {/* Motorun ürettiği gerçek ikon — çıktıdakiyle aynı görsel. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/api/isg-ikonlari/${ad}.png`}
                alt=""
                aria-hidden
                width={32}
                height={32}
                className={cn(
                  "size-8 shrink-0 transition-[filter,opacity] duration-200",
                  secili
                    ? "opacity-100"
                    : "opacity-40 grayscale group-hover:opacity-70",
                )}
              />
              <span
                className={cn(
                  "text-xs leading-tight",
                  secili ? "font-semibold text-foreground" : "text-muted-foreground",
                )}
              >
                {etiket}
              </span>
            </label>
          );
        })}
      </div>

      <p
        className="mt-2.5 text-[11px] leading-snug text-muted-foreground"
        aria-live="polite"
      >
        {secilenler.length === 0
          ? "Hiç seçim yapılmazsa şablonun mevcut piktogramlarına dokunulmaz."
          : `${secilenler.length} ikon seçildi — V7:W7 alanına eşit ölçüde dizilecek.`}
        {secilenler.length > RAHAT_SIGAN && (
          <span className="ml-1 font-semibold text-accent">
            {RAHAT_SIGAN}&apos;ten fazla ikon alana sığması için küçültülür.
          </span>
        )}
      </p>
    </>
  );
}
