import type { CSSProperties } from "react";
import type { BicimKurali } from "@/lib/api";

export interface KayitBicimi {
  kalin: boolean;
  renk: string;
  italik: boolean;
}

const VARSAYILAN: KayitBicimi = { kalin: false, renk: "000000", italik: false };

function kucult(metin: string): string {
  return metin.trim().toLocaleLowerCase("tr");
}

/** Python `KuralMotoru.bicim` ile aynı sıra — ilk uyan kural kazanır. */
export function bicimHesapla(
  alan: string,
  deger: string,
  kurallar: BicimKurali[],
  varsayilan: KayitBicimi = VARSAYILAN,
): KayitBicimi {
  const k = kucult(deger);
  for (const kural of kurallar) {
    if (!kural.etkin || kural.alan !== alan) continue;
    const liste = kural.degerler.map((d) => kucult(d));
    let uyuyor = false;
    switch (kural.operator) {
      case "listede":
        uyuyor = liste.includes(k);
        break;
      case "listede_degil":
        uyuyor = Boolean(k) && !liste.includes(k);
        break;
      case "esittir":
        uyuyor = liste.length > 0 && k === liste[0];
        break;
      case "icerir":
        uyuyor = liste.some((d) => d && k.includes(d));
        break;
      case "bos":
        uyuyor = !k;
        break;
    }
    if (uyuyor) return kural.bicim;
  }
  return varsayilan;
}

export function rgbStili(renk: string, kalin: boolean, italik: boolean): CSSProperties {
  const hex = renk.replace(/^#/, "").padStart(6, "0");
  return {
    color: `#${hex}`,
    fontWeight: kalin ? 700 : 400,
    fontStyle: italik ? "italic" : "normal",
  };
}
