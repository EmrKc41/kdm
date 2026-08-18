"use client";

import { useMemo, useState } from "react";
import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter,
  useSensor, useSensors, type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext, arrayMove, rectSortingStrategy,
  sortableKeyboardCoordinates,
} from "@dnd-kit/sortable";
import { toast } from "sonner";
import { ggaayyyy, bugun } from "@/lib/tarih";
import { SARI_ALAN_SINIRI, type KontrolAdimi, type TalimatVerisi } from "@/lib/types";
import { Alan } from "@/components/ortak/alan";
import { Bolum } from "@/components/ortak/bolum";
import { GorselBirak } from "@/components/ortak/gorsel-birak";
import { EylemCubugu } from "@/components/ortak/eylem-cubugu";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { AdimKarti } from "./adim-karti";
import { IsgSecici } from "./isg-secici";

/* Baslangic kimlikleri DETERMINISTIK olmali: rastgele uretilirse sunucu ve
   istemci render'lari farkli id uretir ve React hydration uyusmazligi verir. */
function bosAdim(sira: number): KontrolAdimi {
  return {
    id: `adim-${sira}`,
    baslik: "", aciklama: "", cycle_sn: "", gorsel: null, gorselAdi: "",
  };
}

function baslangic(): TalimatVerisi {
  return {
    baslik: "", baslik_buyuk_harf: false, konu: "", konu_otomatik_ek: true,
    parca_no: "", parca_adi: "", musteri: "", hazirlama_tarihi: bugun(),
    hazirlayan: "", son_rev_tarihi: "", musteri_temsilcisi: "",
    son_rev_aciklamasi: "", onay: "", isg_ikonlari: [],
    sayfa_no: "1", talimat_no: "", rev_no: "0", tarih: bugun(),
    logo: null, bos_blok_davranisi: "cerceveli",
    adimlar: Array.from({ length: 9 }, (_, i) => bosAdim(i)),
  };
}

export function TalimatFormu() {
  const [v, setV] = useState<TalimatVerisi>(baslangic);

  const yama = <A extends keyof TalimatVerisi>(alan: A, deger: TalimatVerisi[A]) =>
    setV((o) => ({ ...o, [alan]: deger }));

  const adimYama = (id: string, p: Partial<KontrolAdimi>) =>
    setV((o) => ({
      ...o,
      adimlar: o.adimlar.map((a) => (a.id === id ? { ...a, ...p } : a)),
    }));

  const sensorler = useSensors(
    // 6px eşik: kazara sürüklemeyi önler (ui-ux-pro-max: drag-threshold)
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const surukleBitti = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    setV((o) => {
      const eski = o.adimlar.findIndex((a) => a.id === active.id);
      const yeni = o.adimlar.findIndex((a) => a.id === over.id);
      return { ...o, adimlar: arrayMove(o.adimlar, eski, yeni) };
    });
  };

  /** Düğmeyle taşıma — sürüklemenin tek-işaretçili alternatifi. */
  const adimTasi = (kimlik: string, yon: -1 | 1) =>
    setV((o) => {
      const eski = o.adimlar.findIndex((a) => a.id === kimlik);
      const yeni = eski + yon;
      if (eski < 0 || yeni < 0 || yeni >= o.adimlar.length) return o;
      return { ...o, adimlar: arrayMove(o.adimlar, eski, yeni) };
    });

  const doluSayisi = v.adimlar.filter(
    (a) => a.baslik.trim() || a.aciklama.trim() || a.cycle_sn.trim() || a.gorsel,
  ).length;

  const konuOnizleme = useMemo(() => {
    const ham = v.konu.trim();
    if (!ham) return "—";
    return v.konu_otomatik_ek && !ham.toUpperCase().endsWith("HK.")
      ? ham + " İŞ TALİMATI HK."
      : ham;
  }, [v.konu, v.konu_otomatik_ek]);

  function dogrula(): string | null {
    if (!v.baslik.trim()) return "Talimat adı zorunludur.";
    const asan = v.adimlar.findIndex(
      (a) => a.baslik.trim().length + a.aciklama.trim().length > SARI_ALAN_SINIRI,
    );
    if (asan >= 0) {
      return (asan + 1) + ". adımın sarı alan metni " + SARI_ALAN_SINIRI +
        " karakter sınırını aşıyor. Program metni sessizce kırpmaz.";
    }
    return null;
  }

  /** Proje dosyasindan gelen veriyi guvenli bicimde forma uygular.
      Eksik alanlar varsayilanla, adim listesi her zaman 9 elemanla ve
      benzersiz kimliklerle tamamlanir. */
  function projeYukle(gelen: Record<string, unknown>) {
    const t = baslangic();
    const g = gelen as Partial<TalimatVerisi>;

    const adimlar = Array.from({ length: 9 }, (_, i) => {
      const a = (g.adimlar ?? [])[i];
      return a
        ? {
            id: `adim-${i}`,
            baslik: a.baslik ?? "",
            aciklama: a.aciklama ?? "",
            cycle_sn: a.cycle_sn == null ? "" : String(a.cycle_sn),
            gorsel: a.gorsel ?? null,
            gorselAdi: a.gorselAdi ?? "",
          }
        : bosAdim(i);
    });

    setV({
      ...t,
      ...g,
      // Tarihler proje dosyasinda ISO tutulur; yine de savunmaci davraniyoruz.
      hazirlama_tarihi: g.hazirlama_tarihi ?? t.hazirlama_tarihi,
      son_rev_tarihi: g.son_rev_tarihi ?? "",
      tarih: g.tarih ?? t.tarih,
      isg_ikonlari: Array.isArray(g.isg_ikonlari) ? g.isg_ikonlari : [],
      bos_blok_davranisi:
        g.bos_blok_davranisi === "temizle" ? "temizle" : "cerceveli",
      adimlar,
    });
  }

  function govde() {
    return {
      ...v,
      hazirlama_tarihi: ggaayyyy(v.hazirlama_tarihi),
      son_rev_tarihi: ggaayyyy(v.son_rev_tarihi),
      tarih: ggaayyyy(v.tarih),
      adimlar: v.adimlar.map(({ baslik, aciklama, cycle_sn, gorsel }) => ({
        baslik, aciklama, cycle_sn, gorsel,
      })),
    };
  }

  return (
    <div className="space-y-4">
      <Bolum baslik="Başlık ve Konu">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Alan etiket="Talimat Adı" htmlFor="t-baslik" zorunlu className="lg:col-span-2">
            <Input
              id="t-baslik"
              value={v.baslik}
              onChange={(e) => yama("baslik", e.target.value)}
              placeholder="FIREWALL İŞ TALİMATI"
            />
            <label className="flex items-center gap-2 pt-0.5 text-xs text-muted-foreground">
              <Checkbox
                checked={v.baslik_buyuk_harf}
                onCheckedChange={(c) => yama("baslik_buyuk_harf", c === true)}
              />
              Büyük harfe çevir (Türkçe kuralıyla: i&rarr;İ, ı&rarr;I)
            </label>
          </Alan>

          <Alan
            etiket="Konu / Parça Referansı"
            htmlFor="t-konu"
            className="lg:col-span-2"
            ipucu={
              <>
                Çıktı:{" "}
                <span className="font-mono font-semibold text-foreground">
                  {konuOnizleme}
                </span>
              </>
            }
          >
            <Input
              id="t-konu"
              value={v.konu}
              onChange={(e) => yama("konu", e.target.value)}
              placeholder="10598-AG"
              className="font-mono"
            />
            <label className="flex items-center gap-2 pt-0.5 text-xs text-muted-foreground">
              <Checkbox
                checked={v.konu_otomatik_ek}
                onCheckedChange={(c) => yama("konu_otomatik_ek", c === true)}
              />
              Sonuna &quot;İŞ TALİMATI HK.&quot; ekle
            </label>
          </Alan>

          <Alan etiket="Parça No" htmlFor="t-parca-no">
            <Input id="t-parca-no" className="font-mono"
              value={v.parca_no} onChange={(e) => yama("parca_no", e.target.value)} />
          </Alan>
          <Alan etiket="Parça Adı" htmlFor="t-parca-adi">
            <Input id="t-parca-adi"
              value={v.parca_adi} onChange={(e) => yama("parca_adi", e.target.value)} />
          </Alan>
          <Alan etiket="Müşteri" htmlFor="t-musteri"
            ipucu="Bu işletme nereye / ne için üretiyor?" className="sm:col-span-2">
            <Input id="t-musteri" placeholder="FORD OTOSAN"
              value={v.musteri} onChange={(e) => yama("musteri", e.target.value)} />
          </Alan>
        </div>
      </Bolum>

      <Bolum baslik="Hazırlama ve Onay">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Alan etiket="Hazırlayan" htmlFor="t-hazirlayan">
            <Input id="t-hazirlayan" value={v.hazirlayan}
              onChange={(e) => yama("hazirlayan", e.target.value)} />
          </Alan>
          <Alan etiket="Hazırlama Tarihi" htmlFor="t-hz-tarih">
            <Input id="t-hz-tarih" type="date" value={v.hazirlama_tarihi}
              onChange={(e) => yama("hazirlama_tarihi", e.target.value)} />
          </Alan>
          <Alan etiket="Müşteri Temsilcisi" htmlFor="t-temsilci">
            <Input id="t-temsilci" value={v.musteri_temsilcisi}
              onChange={(e) => yama("musteri_temsilcisi", e.target.value)} />
          </Alan>
          <Alan etiket="Onay" htmlFor="t-onay">
            <Input id="t-onay" value={v.onay}
              onChange={(e) => yama("onay", e.target.value)} />
          </Alan>
          <Alan etiket="Son Rev. Tarihi" htmlFor="t-rev-tarih">
            <Input id="t-rev-tarih" type="date" value={v.son_rev_tarihi}
              onChange={(e) => yama("son_rev_tarihi", e.target.value)} />
          </Alan>
          <Alan etiket="Son Rev. Açıklaması" htmlFor="t-rev-aciklama"
            className="sm:col-span-2 lg:col-span-3">
            <Input id="t-rev-aciklama" value={v.son_rev_aciklamasi}
              onChange={(e) => yama("son_rev_aciklamasi", e.target.value)} />
          </Alan>
        </div>
      </Bolum>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.25fr]">
        <Bolum baslik="Doküman Bilgileri">
          <div className="grid gap-4 sm:grid-cols-2">
            <Alan etiket="Sayfa No" htmlFor="t-sayfa">
              <Input id="t-sayfa" className="font-mono" value={v.sayfa_no}
                onChange={(e) => yama("sayfa_no", e.target.value)} />
            </Alan>
            <Alan etiket="Talimat No" htmlFor="t-talimat-no">
              <Input id="t-talimat-no" className="font-mono" placeholder="BC-F-0139"
                value={v.talimat_no} onChange={(e) => yama("talimat_no", e.target.value)} />
            </Alan>
            <Alan etiket="Rev. No" htmlFor="t-rev-no">
              <Input id="t-rev-no" className="font-mono" value={v.rev_no}
                onChange={(e) => yama("rev_no", e.target.value)} />
            </Alan>
            <Alan etiket="Tarih" htmlFor="t-tarih">
              <Input id="t-tarih" type="date" value={v.tarih}
                onChange={(e) => yama("tarih", e.target.value)} />
            </Alan>
            <div className="sm:col-span-2">
              <GorselBirak
                deger={v.logo}
                onDegisim={(g) => yama("logo", g)}
                etiket="Kurum Logosu"
                ipucu="Çıktıda tam 1,55 × 3,28 cm — F6:G7 alanındaki SC sembolü sabittir, değişmez"
                yukseklikSinifi="h-24"
              />
            </div>
          </div>
        </Bolum>

        <Bolum baslik="İSG Ekipmanı" aciklama="ISO 7010 — mavi daire, beyaz sembol">
          <IsgSecici
            secilenler={v.isg_ikonlari}
            onDegisim={(s) => yama("isg_ikonlari", s)}
          />
        </Bolum>
      </div>

      <Bolum
        baslik="Kontrol Adımları"
        aciklama="Kartı tutamağından sürükleyerek sırayı değiştirin"
        eylem={
          <Badge variant={doluSayisi ? "default" : "secondary"} className="font-mono">
            {doluSayisi} / 9 dolu
          </Badge>
        }
      >
        <fieldset className="mb-4">
          <legend className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Doldurulmayan bloklar
          </legend>
          <RadioGroup
            value={v.bos_blok_davranisi}
            onValueChange={(d) =>
              yama("bos_blok_davranisi", d as TalimatVerisi["bos_blok_davranisi"])
            }
            className="flex flex-wrap gap-x-6 gap-y-2"
          >
            <div className="flex items-center gap-2">
              <RadioGroupItem value="cerceveli" id="bb-cerceveli" />
              <Label htmlFor="bb-cerceveli" className="text-sm font-normal">
                Boş ama çerçeveli bırak
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <RadioGroupItem value="temizle" id="bb-temizle" />
              <Label htmlFor="bb-temizle" className="text-sm font-normal">
                Başlık ve cycle kutularını temizle
              </Label>
            </div>
          </RadioGroup>
        </fieldset>

        {/* Sabit id: dnd-kit erisilebilirlik duyuru kimliklerini bu id'den
            turetir. Verilmezse modul duzeyinde bir sayac kullanir ve sunucu
            ile istemci farkli deger uretip hydration uyusmazligi olusturur. */}
        <DndContext
          id="kontrol-adimlari"
          sensors={sensorler}
          collisionDetection={closestCenter}
          onDragEnd={surukleBitti}
        >
          <SortableContext items={v.adimlar.map((a) => a.id)} strategy={rectSortingStrategy}>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {v.adimlar.map((adim, i) => (
                <AdimKarti
                  key={adim.id}
                  adim={adim}
                  sira={i + 1}
                  toplam={v.adimlar.length}
                  onTasi={(yon) => adimTasi(adim.id, yon)}
                  onDegisim={(p) => adimYama(adim.id, p)}
                  onTemizle={() =>
                    adimYama(adim.id, {
                      baslik: "", aciklama: "", cycle_sn: "", gorsel: null, gorselAdi: "",
                    })
                  }
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </Bolum>

      <EylemCubugu
        tip="talimat"
        dogrula={dogrula}
        govde={govde}
        proje={() => v}
        onProjeYukle={projeYukle}
        onSifirla={() => {
          setV(baslangic());
          toast.success("Form temizlendi.");
        }}
        durum={doluSayisi + " adım dolu"}
      />
    </div>
  );
}
