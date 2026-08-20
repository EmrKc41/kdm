"use client";

import { useState } from "react";
import { PencilLine } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ggaayyyy, bugun } from "@/lib/tarih";
import { EGITIM_ICERIGI, EGITIM_TURU, type TneVerisi } from "@/lib/types";
import { Alan } from "@/components/ortak/alan";
import { Bolum } from "@/components/ortak/bolum";
import { GorselBirak } from "@/components/ortak/gorsel-birak";
import { EylemCubugu } from "@/components/ortak/eylem-cubugu";
import { Input } from "@/components/ui/input";

/** Sahada kalemle doldurulacağı için programın sormadığı alanlar. */
const ELLE_DOLDURULACAK = [
  "Konu · Müdürlük / Birim · Kısım · Hazırlayan",
  "Parametre · Ölçüm Aracı · Parça Üzerindeki Etkisi · TND No",
  "Sayfa No · Talimat No · Rev. No",
  "Eğitimi alan · Sicil no · İmza satırlarının tamamı (satır 11–42)",
];

function baslangic(): TneVerisi {
  return {
    egitim_icerigi: [], egitim_turu: [], egitim_suresi: "",
    sorumlu: "", egitim_veren: "", egitim_tarihi: bugun(), tarih: bugun(),
    egitim_gorseli: null,
  };
}

interface KutuIzgaraOzellikleri {
  secenekler: readonly string[];
  secilenler: string[];
  onDegisim: (s: string[]) => void;
  etiket: string;
}

function KutuIzgara({ secenekler, secilenler, onDegisim, etiket }: KutuIzgaraOzellikleri) {
  return (
    <div role="group" aria-label={etiket} className="flex flex-wrap gap-2">
      {secenekler.map((ad) => {
        const secili = secilenler.includes(ad);
        return (
          <label
            key={ad}
            className={cn(
              "flex items-center gap-2 rounded-md border px-3 py-2 text-sm",
              "transition-all duration-200",
              "has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring has-[:focus-visible]:ring-offset-1",
              secili
                ? "border-[var(--excel-yesil)] bg-[var(--excel-yesil)]/10 font-semibold"
                : "border-input bg-card text-muted-foreground hover:border-primary/60",
            )}
          >
            <input
              type="checkbox"
              name={etiket}
              value={ad}
              checked={secili}
              onChange={() =>
                onDegisim(
                  secili ? secilenler.filter((x) => x !== ad) : [...secilenler, ad],
                )
              }
              className="sr-only"
            />
            {/* Çıktıdaki yeşil dolgunun birebir aynası */}
            <span
              className={cn(
                "size-3.5 shrink-0 rounded-[2px] border transition-colors duration-200",
                secili
                  ? "border-[var(--excel-yesil)] bg-[var(--excel-yesil)]"
                  : "border-muted-foreground/50 bg-transparent",
              )}
              aria-hidden
            />
            {ad}
          </label>
        );
      })}
    </div>
  );
}

export function TneFormu() {
  const [v, setV] = useState<TneVerisi>(baslangic);

  const yama = <A extends keyof TneVerisi>(alan: A, deger: TneVerisi[A]) =>
    setV((o) => ({ ...o, [alan]: deger }));

  const secim = v.egitim_icerigi.length + v.egitim_turu.length;

  return (
    <div className="space-y-4">
      <Bolum
        baslik="Eğitim İçeriği ve Türü"
        aciklama="Seçilenler çıktıda yeşil dolgu alır; şablonda hazır gelen işaretler seçilmediyse temizlenir"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Eğitim İçeriği
            </span>
            <KutuIzgara
              etiket="Eğitim içeriği"
              secenekler={EGITIM_ICERIGI}
              secilenler={v.egitim_icerigi}
              onDegisim={(s) => yama("egitim_icerigi", s)}
            />
          </div>
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Eğitim Türü
            </span>
            <KutuIzgara
              etiket="Eğitim türü"
              secenekler={EGITIM_TURU}
              secilenler={v.egitim_turu}
              onDegisim={(s) => yama("egitim_turu", s)}
            />
          </div>
        </div>
      </Bolum>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
        <Bolum baslik="Eğitim Bilgileri">
          <div className="grid gap-4 sm:grid-cols-2">
            <Alan etiket="Eğitim Süresi" htmlFor="e-sure">
              <Input id="e-sure" placeholder="15 DK" className="font-mono"
                value={v.egitim_suresi} onChange={(e) => yama("egitim_suresi", e.target.value)} />
            </Alan>
            <Alan etiket="Tarih" htmlFor="e-tarih">
              <Input id="e-tarih" type="date" value={v.egitim_tarihi}
                onChange={(e) => {
                  yama("egitim_tarihi", e.target.value);
                  yama("tarih", e.target.value);
                }} />
            </Alan>
            <Alan etiket="Sorumlu" htmlFor="e-sorumlu">
              <Input id="e-sorumlu" value={v.sorumlu}
                onChange={(e) => yama("sorumlu", e.target.value)} />
            </Alan>
            <Alan etiket="Eğitim Veren" htmlFor="e-veren">
              <Input id="e-veren" value={v.egitim_veren}
                onChange={(e) => yama("egitim_veren", e.target.value)} />
            </Alan>
          </div>
        </Bolum>

        <Bolum baslik="Parça Resmi" aciklama="B11:G42 — çıktıda tam 41,75 × 23,72 cm">
          <GorselBirak
            deger={v.egitim_gorseli}
            onDegisim={(g) => yama("egitim_gorseli", g)}
            etiket="Parça Resmi"
            ipucu="Kutuyu tamamen doldurur: oranı korunur, taşan kenarlar kırpılır"
            yukseklikSinifi="h-48"
          />
        </Bolum>
      </div>

      <Bolum baslik="Sahada Elle Doldurulacak Alanlar">
        <div className="flex gap-3">
          <PencilLine
            className="mt-0.5 size-4 shrink-0 text-muted-foreground"
            aria-hidden
          />
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Aşağıdaki alanlar çıktıda{" "}
              <strong className="text-foreground">boş ve çerçeveli</strong> bırakılır;
              eğitim sırasında kalemle doldurulur. Bu yüzden burada sorulmuyor:
            </p>
            <ul className="space-y-1 text-xs text-muted-foreground">
              {ELLE_DOLDURULACAK.map((satir) => (
                <li key={satir} className="flex gap-2">
                  <span className="text-muted-foreground/50" aria-hidden>
                    &bull;
                  </span>
                  {satir}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Bolum>

      <EylemCubugu
        tip="tne"
        dogrula={() => null}
        proje={() => v}
        onProjeYukle={(gelen) => {
          const g = gelen as Partial<TneVerisi>;
          setV({
            ...baslangic(),
            ...g,
            egitim_icerigi: Array.isArray(g.egitim_icerigi) ? g.egitim_icerigi : [],
            egitim_turu: Array.isArray(g.egitim_turu) ? g.egitim_turu : [],
          });
        }}
        govde={() => ({
          ...v,
          egitim_tarihi: ggaayyyy(v.egitim_tarihi),
          tarih: ggaayyyy(v.tarih),
        })}
        onSifirla={() => {
          setV(baslangic());
          toast.success("Form temizlendi.");
        }}
        durum={secim + " seçim"}
      />
    </div>
  );
}
