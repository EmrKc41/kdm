"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { yeniId } from "@/lib/dosya";
import { bugun, ggaayyyy } from "@/lib/tarih";
import type { RaporSatiri, RaporVerisi } from "@/lib/types";
import { Alan } from "@/components/ortak/alan";
import { Bolum } from "@/components/ortak/bolum";
import { EylemCubugu } from "@/components/ortak/eylem-cubugu";
import { DurumPili } from "@/components/rapor/durum-pili";
import { RaporOnizleme } from "@/components/rapor/rapor-onizleme";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DURUMLAR = ["Açık", "Devam Ediyor", "Kapalı"] as const;

const SUTUNLAR = [
  { alan: "tanim", etiket: "Uygunsuzluk Tanımı", genislik: "min-w-48" },
  { alan: "kok_neden", etiket: "Kök Neden", genislik: "min-w-36" },
  { alan: "duzeltici_faaliyet", etiket: "Düzeltici Faaliyet", genislik: "min-w-44" },
  { alan: "sorumlu", etiket: "Sorumlu", genislik: "min-w-32" },
  { alan: "hedef_tarih", etiket: "Hedef Tarih", genislik: "min-w-28" },
  { alan: "durum", etiket: "Durum", genislik: "min-w-28" },
] as const;

type SatirAlan = (typeof SUTUNLAR)[number]["alan"];

function bosSatir(id: string): RaporSatiri {
  return {
    id,
    tanim: "",
    kok_neden: "",
    duzeltici_faaliyet: "",
    sorumlu: "",
    hedef_tarih: "",
    durum: "Açık",
  };
}

function baslangic(): RaporVerisi {
  return {
    baslik: "KALİTE UYGUNSUZLUK TAKİP RAPORU",
    konu: "",
    rapor_no: "",
    tarih: bugun(),
    hazirlayan: "",
    genel_durum: "Açık",
    ozet: "",
    satirlar: Array.from({ length: 3 }, (_, i) => bosSatir(String(i))),
  };
}

export function RaporFormu() {
  const [v, setV] = useState<RaporVerisi>(baslangic);

  const satirYama = (id: string, alan: SatirAlan, deger: string) =>
    setV((o) => ({
      ...o,
      satirlar: o.satirlar.map((s) => (s.id === id ? { ...s, [alan]: deger } : s)),
    }));

  const satirEkle = () =>
    setV((o) => ({ ...o, satirlar: [...o.satirlar, bosSatir(yeniId())] }));

  const satirSil = (id: string) =>
    setV((o) => ({
      ...o,
      satirlar: o.satirlar.length > 1 ? o.satirlar.filter((s) => s.id !== id) : o.satirlar,
    }));

  const doluSatir = v.satirlar.filter(
    (s) => s.tanim.trim() || s.kok_neden.trim() || s.duzeltici_faaliyet.trim(),
  ).length;

  const govde = () => ({
    ...v,
    tarih: ggaayyyy(v.tarih),
    satirlar: v.satirlar.map(
      ({ tanim, kok_neden, duzeltici_faaliyet, sorumlu, hedef_tarih, durum }) => ({
        tanim,
        kok_neden,
        duzeltici_faaliyet,
        sorumlu,
        hedef_tarih: hedef_tarih ? ggaayyyy(hedef_tarih) : "",
        durum,
      }),
    ),
  });

  return (
    <div className="space-y-4 pb-20">
      <Bolum baslik="Excel Önizleme" aciklama="Çıktıdaki kurumsal bant ve tablo düzeni">
        <RaporOnizleme veri={v} />
      </Bolum>

      <Bolum baslik="Rapor Kimliği">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Alan etiket="Başlık" htmlFor="r-baslik">
            <Input
              id="r-baslik"
              value={v.baslik}
              onChange={(e) => setV({ ...v, baslik: e.target.value })}
            />
          </Alan>
          <Alan etiket="Konu / Parça *" htmlFor="r-konu">
            <Input
              id="r-konu"
              value={v.konu}
              onChange={(e) => setV({ ...v, konu: e.target.value })}
              placeholder="10598-AG"
            />
          </Alan>
          <Alan etiket="Rapor No" htmlFor="r-rapor-no">
            <Input
              id="r-rapor-no"
              value={v.rapor_no}
              onChange={(e) => setV({ ...v, rapor_no: e.target.value })}
            />
          </Alan>
          <Alan etiket="Tarih" htmlFor="r-tarih">
            <Input
              id="r-tarih"
              type="date"
              value={v.tarih}
              onChange={(e) => setV({ ...v, tarih: e.target.value })}
            />
          </Alan>
          <Alan etiket="Hazırlayan" htmlFor="r-hazirlayan">
            <Input
              id="r-hazirlayan"
              value={v.hazirlayan}
              onChange={(e) => setV({ ...v, hazirlayan: e.target.value })}
            />
          </Alan>
          <Alan etiket="Genel Durum">
            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={v.genel_durum}
                onValueChange={(deger) => setV({ ...v, genel_durum: deger })}
              >
                <SelectTrigger className="min-w-40" aria-label="Genel Durum">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DURUMLAR.map((d) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <DurumPili durum={v.genel_durum} />
            </div>
          </Alan>
        </div>
      </Bolum>

      <Bolum baslik="Özet">
        <Textarea
          id="r-ozet"
          aria-label="Özet"
          value={v.ozet}
          onChange={(e) => setV({ ...v, ozet: e.target.value })}
          rows={3}
          placeholder="Uygunsuzluğun kısa özeti…"
        />
      </Bolum>

      <Bolum
        baslik="Uygunsuzluk Satırları"
        aciklama={`${doluSatir} dolu satır`}
        eylem={
          <Button size="sm" variant="outline" onClick={satirEkle}>
            <Plus className="size-4" aria-hidden /> Satır Ekle
          </Button>
        }
      >
        <div className="overflow-x-auto kaydirma-ince">
          <table className="w-full min-w-[960px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-2 py-2 text-left text-[11px] font-bold uppercase tracking-wide text-muted-foreground w-8">
                  #
                </th>
                {SUTUNLAR.map((s) => (
                  <th
                    key={s.alan}
                    className={`px-2 py-2 text-left text-[11px] font-bold uppercase tracking-wide text-muted-foreground ${s.genislik}`}
                  >
                    {s.etiket}
                  </th>
                ))}
                <th className="w-10" />
              </tr>
            </thead>
            <tbody>
              {v.satirlar.map((satir, i) => (
                <tr key={satir.id} className="border-b border-border/60">
                  <td className="px-2 py-1 font-mono text-xs text-muted-foreground">{i + 1}</td>
                  {SUTUNLAR.map((s) => (
                    <td key={s.alan} className="px-1 py-1">
                      {s.alan === "durum" ? (
                        <div className="flex flex-col gap-1">
                          <Select
                            value={satir.durum || "Açık"}
                            onValueChange={(deger) => satirYama(satir.id, "durum", deger)}
                          >
                            <SelectTrigger className="h-8 text-xs" aria-label={`${i + 1}. satır Durum`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {DURUMLAR.map((d) => (
                                <SelectItem key={d} value={d}>{d}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <DurumPili durum={satir.durum || "Açık"} className="w-fit" />
                        </div>
                      ) : s.alan === "hedef_tarih" ? (
                        <Input
                          type="date"
                          className="h-8 text-xs"
                          aria-label={`${i + 1}. satır Hedef Tarih`}
                          value={satir.hedef_tarih}
                          onChange={(e) => satirYama(satir.id, "hedef_tarih", e.target.value)}
                        />
                      ) : (
                        <Input
                          className="h-8 text-xs"
                          aria-label={`${i + 1}. satır ${s.etiket}`}
                          value={satir[s.alan]}
                          onChange={(e) => satirYama(satir.id, s.alan, e.target.value)}
                        />
                      )}
                    </td>
                  ))}
                  <td className="px-1 py-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="size-8 text-muted-foreground hover:text-destructive"
                      onClick={() => satirSil(satir.id)}
                      aria-label={`${i + 1}. satırı sil`}
                    >
                      <Trash2 className="size-3.5" aria-hidden />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Bolum>

      <EylemCubugu
        tip="rapor"
        dogrula={() => (v.konu.trim() ? null : "Konu / parça referansı zorunludur.")}
        govde={govde}
        proje={() => v}
        onProjeYukle={(veri) => setV({ ...baslangic(), ...veri } as RaporVerisi)}
        onSifirla={() => setV(baslangic())}
        durum={`${doluSatir} satır`}
      />
    </div>
  );
}
