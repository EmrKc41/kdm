"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const SIRA = ["light", "dark", "system"] as const;
type Tema = (typeof SIRA)[number];

const ETIKET: Record<Tema, string> = {
  light: "Açık tema",
  dark: "Koyu tema",
  system: "Sistem teması",
};

const IKON = { light: Sun, dark: Moon, system: Monitor } as const;

export function TemaDugmesi() {
  const { theme, setTheme } = useTheme();

  /* Sunucuda tema bilinmez; istemci ise localStorage'dan okur. Bu yüzden
     temaya bagli HER CIKTI (ikon, aria-label, tooltip) ilk render'da notr
     olmali — yalnizca ikonu koşullamak yetmez, erisilebilirlik etiketi de
     sunucu/istemci arasinda ayrisir ve hydration uyusmazligi verir.

     useEffect + setState yerine useSyncExternalStore: efekt icinde durum
     guncellemek fazladan bir render turu olusturur ve React 19 lint
     kurallarina takilir. */
  const binmis = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const aktif: Tema = binmis ? ((theme as Tema) ?? "system") : "system";
  const sonraki = SIRA[(SIRA.indexOf(aktif) + 1) % SIRA.length];
  const Ikon = IKON[aktif];

  // Tema okunana kadar hangi moda gecilecegi bilinemez; notr metin kullanilir.
  const etiket = binmis
    ? `${ETIKET[aktif]} — ${ETIKET[sonraki]} moduna geç`
    : "Tema değiştir";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(sonraki)}
          aria-label={etiket}
        >
          <Ikon className="size-4" aria-hidden />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{binmis ? ETIKET[sonraki] : "Tema değiştir"}</TooltipContent>
    </Tooltip>
  );
}
