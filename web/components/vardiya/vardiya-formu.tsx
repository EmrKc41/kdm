"use client";

import { useEffect, useRef, useState } from "react";
import { FileUp, Plus, Trash2, Users } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { personelIceAktar, unvanlariGetir } from "@/lib/api";
import { dataUrlOku, yeniId } from "@/lib/dosya";
import { ggaayyyy, bugun, haftaAdi } from "@/lib/tarih";
import {
  VARDIYA_SAATLERI,
  type HaftalikVardiya,
  type VardiyaHarfi,
  type VardiyaKaydi,
} from "@/lib/types";
import { Alan } from "@/components/ortak/alan";
import { Bolum } from "@/components/ortak/bolum";
import { EylemCubugu } from "@/components/ortak/eylem-cubugu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const HARFLER: VardiyaHarfi[] = ["A", "B", "C"];

/** Her vardiyanın kendi bant rengi — çıktıdaki renklerle aynı. */
const VARDIYA_RENGI: Record<VardiyaHarfi, string> = {
  A: "#1F3864",
  B: "#1E6B4F",
  C: "#7A3E12",
};

const SUTUNLAR = [
  { alan: "ad_soyad", etiket: "Ad Soyad", genislik: "min-w-48" },
  { alan: "unvan", etiket: "Ünvan", genislik: "min-w-40" },
  { alan: "calisma_yeri", etiket: "Çalışacağı Yer / Hat", genislik: "min-w-44" },
  { alan: "telefon", etiket: "Telefon No", genislik: "min-w-36" },
  { alan: "durak", etiket: "Durak İsmi", genislik: "min-w-40" },
] as const;

function bosKayit(id: string): VardiyaKaydi {
  return { id, ad_soyad: "", unvan: "", calisma_yeri: "", telefon: "", durak: "" };
}

function baslangic(): HaftalikVardiya {
  return {
    tarih: bugun(),
    normal_unvanlar: ["Kalite Operatörü"],
    vardiyalar: HARFLER.map((h) => ({
      vardiya_adi: h,
      vardiya_saati: VARDIYA_SAATLERI[h],
      /* Deterministik kimlik: hydration uyusmazligini onler. */
      kayitlar: Array.from({ length: 5 }, (_, i) => bosKayit(`${h}-${i}`)),
    })),
  };
}

export function VardiyaFormu() {
  const [v, setV] = useState<HaftalikVardiya>(baslangic);
  const [aktif, setAktif] = useState<VardiyaHarfi>("B");
  const dosyaRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    unvanlariGetir()
      .then((u) => u.length && setV((o) => ({ ...o, normal_unvanlar: u })))
      .catch(() => { /* motor kapalıysa varsayılan liste kullanılır */ });
  }, []);

  const blok = v.vardiyalar.find((b) => b.vardiya_adi === aktif)!;
  const normalKucuk = v.normal_unvanlar.map((u) => u.toLocaleLowerCase("tr"));

  /** Kural motorunun aynası: listede olmayan ünvan vurgulanır. */
  const vurgulu = (unvan: string) => {
    const u = unvan.trim().toLocaleLowerCase("tr");
    return Boolean(u) && !normalKucuk.includes(u);
  };

  const blokYama = (harf: VardiyaHarfi, yeni: Partial<HaftalikVardiya["vardiyalar"][0]>) =>
    setV((o) => ({
      ...o,
      vardiyalar: o.vardiyalar.map((b) =>
        b.vardiya_adi === harf ? { ...b, ...yeni } : b,
      ),
    }));

  const kayitYama = (id: string, alan: keyof VardiyaKaydi, deger: string) =>
    blokYama(aktif, {
      kayitlar: blok.kayitlar.map((k) => (k.id === id ? { ...k, [alan]: deger } : k)),
    });

  // Kullanici etkilesimiyle eklenen satirlar yalnizca istemcide olusur;
  // burada rastgele kimlik guvenlidir.
  const satirEkle = () =>
    blokYama(aktif, { kayitlar: [...blok.kayitlar, bosKayit(yeniId())] });

  const satirSil = (id: string) =>
    blokYama(aktif, { kayitlar: blok.kayitlar.filter((k) => k.id !== id) });

  async function iceAktar(dosya: File | undefined) {
    if (!dosya) return;
    try {
      const kayitlar = await personelIceAktar(dosya.name, await dataUrlOku(dosya));
      blokYama(aktif, {
        kayitlar: [
          ...blok.kayitlar.filter((k) => k.ad_soyad.trim()),
          ...kayitlar.map((k) => ({ ...k, id: yeniId() })),
        ],
      });
      toast.success(kayitlar.length + " kayıt içe aktarıldı.", {
        description: aktif + " vardiyasına eklendi.",
      });
    } catch (e) {
      const m = e as { mesaj?: string; message?: string; detay?: string };
      toast.error(m.mesaj ?? m.message ?? "Dosya işlenemedi.", {
        description: m.detay,
      });
    } finally {
      if (dosyaRef.current) dosyaRef.current.value = "";
    }
  }

  const doluSayisi = (harf: VardiyaHarfi) =>
    v.vardiyalar.find((b) => b.vardiya_adi === harf)!.kayitlar
      .filter((k) => k.ad_soyad.trim()).length;

  const toplam = HARFLER.reduce((t, h) => t + doluSayisi(h), 0);

  function govde() {
    return {
      tarih: ggaayyyy(v.tarih),
      normal_unvanlar: v.normal_unvanlar,
      vardiyalar: v.vardiyalar.map((b) => ({
        vardiya_adi: b.vardiya_adi,
        vardiya_saati: b.vardiya_saati,
        kayitlar: b.kayitlar
          .filter((k) => k.ad_soyad.trim())
          .map(({ ad_soyad, unvan, calisma_yeri, telefon, durak }) => ({
            ad_soyad, unvan, calisma_yeri, telefon, durak,
          })),
      })),
    };
  }

  return (
    <div className="space-y-4">
      <Bolum
        baslik="Vardiya Seçimi"
        aciklama="Üç vardiya tek sayfada yan yana yazılır"
        eylem={
          <Badge variant="outline" className="font-mono">
            {haftaAdi(v.tarih) || "—"}
          </Badge>
        }
      >
        <div role="tablist" aria-label="Vardiya seçimi" className="flex flex-wrap gap-2">
          {HARFLER.map((harf) => {
            const secili = harf === aktif;
            const adet = doluSayisi(harf);
            return (
              <button
                key={harf}
                role="tab"
                type="button"
                aria-selected={secili}
                onClick={() => setAktif(harf)}
                className={cn(
                  "min-w-44 rounded-md border px-4 py-2.5 text-left",
                  "transition-all duration-200",
                  secili
                    ? "border-transparent text-white shadow-sm"
                    : "border-input bg-card hover:border-primary/60",
                )}
                style={secili ? { backgroundColor: VARDIYA_RENGI[harf] } : undefined}
              >
                <span className="block text-sm font-bold">{harf} VARDİYASI</span>
                <span
                  className={cn(
                    "block font-mono text-xs",
                    secili ? "text-white/75" : "text-muted-foreground",
                  )}
                >
                  {VARDIYA_SAATLERI[harf]}
                </span>
                <span
                  className={cn(
                    "mt-0.5 block text-[11px]",
                    secili ? "text-white/60" : "text-muted-foreground/70",
                  )}
                >
                  {adet ? adet + " kayıt" : "boş"}
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Alan etiket="Tarih" htmlFor="v-tarih" ipucu="Sayfa adı bu tarihten türetilir">
            <Input id="v-tarih" type="date" value={v.tarih}
              onChange={(e) => setV((o) => ({ ...o, tarih: e.target.value }))} />
          </Alan>
          <Alan
            etiket={aktif + " Vardiyası Saati"}
            htmlFor="v-saat"
            ipucu="Harfe göre otomatik gelir, elle değiştirilebilir"
          >
            <Input id="v-saat" className="font-mono" value={blok.vardiya_saati}
              onChange={(e) => blokYama(aktif, { vardiya_saati: e.target.value })} />
          </Alan>
        </div>
      </Bolum>

      <Bolum
        baslik={aktif + " Vardiyası Personel Listesi"}
        aciklama="Ünvanı normal listede olmayan satırlar çıktıda kırmızı ve kalın yazılır"
        eylem={
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={satirEkle}>
              <Plus className="size-4" aria-hidden /> Satır Ekle
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => dosyaRef.current?.click()}
            >
              <FileUp className="size-4" aria-hidden /> CSV / Excel
            </Button>
            <input
              ref={dosyaRef}
              type="file"
              accept=".csv,.xlsx,.xlsm,.txt"
              className="sr-only"
              onChange={(e) => void iceAktar(e.target.files?.[0])}
              aria-label="Personel listesi içe aktar"
            />
            <Badge variant="secondary" className="font-mono">
              {doluSayisi(aktif)} kayıt
            </Badge>
          </div>
        }
      >
        {blok.kayitlar.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-center">
            <Users className="size-8 text-muted-foreground/40" aria-hidden />
            <p className="text-sm text-muted-foreground">
              {aktif} vardiyasında henüz kayıt yok.
            </p>
            <Button size="sm" variant="outline" onClick={satirEkle}>
              <Plus className="size-4" aria-hidden /> İlk satırı ekle
            </Button>
          </div>
        ) : (
          <div className="kaydirma-ince overflow-x-auto rounded-md border border-border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr style={{ backgroundColor: VARDIYA_RENGI[aktif] }}>
                  <th className="w-12 px-2 py-2 text-center text-[11px] font-bold uppercase tracking-wide text-white">
                    #
                  </th>
                  {SUTUNLAR.map((s) => (
                    <th
                      key={s.alan}
                      className={cn(
                        "px-2 py-2 text-left text-[11px] font-bold uppercase tracking-wide text-white",
                        s.genislik,
                      )}
                    >
                      {s.etiket}
                    </th>
                  ))}
                  <th className="w-12 px-2 py-2">
                    <span className="sr-only">İşlem</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {blok.kayitlar.map((k, i) => {
                  const kirmizi = vurgulu(k.unvan);
                  return (
                    <tr
                      key={k.id}
                      className={cn(
                        "border-t border-border transition-colors duration-150",
                        "hover:bg-muted/60",
                        i % 2 === 1 && "bg-muted/25",
                      )}
                    >
                      <td className="px-2 py-1 text-center font-mono text-xs tabular-nums text-muted-foreground">
                        {i + 1}
                      </td>
                      {SUTUNLAR.map((s) => (
                        <td key={s.alan} className="p-0">
                          <input
                            value={k[s.alan]}
                            onChange={(e) => kayitYama(k.id, s.alan, e.target.value)}
                            aria-label={`${i + 1}. satır ${s.etiket}`}
                            inputMode={s.alan === "telefon" ? "tel" : undefined}
                            className={cn(
                              "w-full bg-transparent px-2 py-1.5 outline-none",
                              "focus-visible:bg-background focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
                              s.alan === "telefon" && "font-mono",
                              kirmizi && "font-bold text-destructive",
                            )}
                          />
                        </td>
                      ))}
                      <td className="px-1 text-center">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => satirSil(k.id)}
                          aria-label={`${i + 1}. satırı sil`}
                          className="size-7 text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="size-3.5" aria-hidden />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Bolum>

      <EylemCubugu
        tip="vardiya"
        dogrula={() => null}
        govde={govde}
        /* Proje dosyasi UC VARDIYAYI BIRDEN tasir; yalnizca ekranda
           acik olan vardiya degil. */
        proje={() => v}
        onProjeYukle={(gelen) => {
          const t = baslangic();
          const g = gelen as Partial<HaftalikVardiya>;

          const vardiyalar = HARFLER.map((h, hi) => {
            const b = (g.vardiyalar ?? []).find(
              (x) => String(x?.vardiya_adi).toUpperCase().startsWith(h),
            );
            const kayitlar = (b?.kayitlar ?? []).map((k, ki) => ({
              ...bosKayit(`${h}-y${ki}`),
              ...k,
              id: `${h}-y${ki}`,
            }));
            return {
              vardiya_adi: h,
              vardiya_saati: b?.vardiya_saati || VARDIYA_SAATLERI[h],
              // Bos vardiyada elle doldurmak icin birkac satir birakilir.
              kayitlar: kayitlar.length
                ? kayitlar
                : t.vardiyalar[hi].kayitlar,
            };
          });

          setV({
            tarih: g.tarih || t.tarih,
            normal_unvanlar: Array.isArray(g.normal_unvanlar) && g.normal_unvanlar.length
              ? g.normal_unvanlar
              : t.normal_unvanlar,
            vardiyalar,
          });
          setAktif("B");
        }}
        onSifirla={() => {
          setV(baslangic());
          setAktif("B");
          toast.success("Tüm vardiyalar temizlendi.");
        }}
        durum={`A:${doluSayisi("A")} · B:${doluSayisi("B")} · C:${doluSayisi("C")} — toplam ${toplam}`}
      />
    </div>
  );
}
