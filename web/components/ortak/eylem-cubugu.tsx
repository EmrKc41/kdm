"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { AlertCircle, Download, FileDown, FolderOpen, Loader2, RotateCcw, Save, X } from "lucide-react";
import { toast } from "sonner";
import { MotorHatasi, belgeUret, bosSablonIndir } from "@/lib/api";
import { ProjeHatasi, projeIndir, projeOku, type ProjeTipi } from "@/lib/proje";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface Ozellikler {
  tip: ProjeTipi;
  /** Hata metni döndürürse üretim yapılmaz. */
  dogrula: () => string | null;
  /** Motora gönderilecek gövde (tarihler GG.AA.YYYY biçimine çevrilmiş). */
  govde: () => unknown;
  /** Proje dosyasına yazılacak HAM form durumu. */
  proje: () => unknown;
  /** Proje dosyasından okunan durumu forma uygular. */
  onProjeYukle: (veri: Record<string, unknown>) => void;
  onSifirla: () => void;
  durum?: string;
}

function hataGoster(e: unknown) {
  if (e instanceof MotorHatasi) {
    toast.error(e.mesaj, { description: e.detay, duration: 12_000 });
    return;
  }
  if (e instanceof ProjeHatasi) {
    toast.error(e.mesaj, { duration: 10_000 });
    return;
  }
  toast.error("Beklenmeyen bir sorun oluştu.");
}

export function EylemCubugu({
  tip, dogrula, govde, proje, onProjeYukle, onSifirla, durum,
}: Ozellikler) {
  const [uretiliyor, setUretiliyor] = useState(false);
  const [sablonIniyor, setSablonIniyor] = useState(false);
  /* Doğrulama hatası yalnızca toast ile verilirse klavye ve ekran okuyucu
     kullanıcısı hatayı kaçırır; toast odak almaz ve kendiliğinden kaybolur.
     Bu yüzden hata ayrıca kalıcı, odaklanabilir bir bölgede duyurulur. */
  const [hata, setHata] = useState<string | null>(null);
  /* Odaklanma sayacı: aynı hata üst üste iki kez oluştuğunda metin
     değişmediği için efekt yeniden çalışmaz; sayaç her denemede artar. */
  const [odakNo, setOdakNo] = useState(0);
  const hataRef = useRef<HTMLDivElement>(null);
  const azHareket = useReducedMotion();
  const dosyaRef = useRef<HTMLInputElement>(null);
  const uretRef = useRef<() => Promise<void>>(async () => {});
  const projeKaydetRef = useRef<() => void>(() => {});

  async function uret() {
    const sorun = dogrula();
    if (sorun) {
      /* Toast BILEREK yok: uyarı bölgesi zaten role="alert" ile duyuruluyor
         ve odağı alıyor. İkisi birden, ekran okuyucuda aynı metni iki kez
         okutur. Toast, motorun döndürdüğü hatalar için saklı (hataGoster). */
      setHata(sorun);
      setOdakNo((n) => n + 1);
      return;
    }
    setHata(null);
    setUretiliyor(true);
    try {
      const ad = await belgeUret(`/api/${tip}`, govde());
      toast.success("Dosya indirildi.", { description: ad });
    } catch (e) {
      hataGoster(e);
    } finally {
      setUretiliyor(false);
    }
  }

  async function sablon() {
    setSablonIniyor(true);
    try {
      const ad = await bosSablonIndir(tip);
      toast.success("Boş şablon indirildi.", { description: ad });
    } catch (e) {
      hataGoster(e);
    } finally {
      setSablonIniyor(false);
    }
  }

  function projeKaydet() {
    try {
      const ad = projeIndir(tip, proje());
      toast.success("Proje kaydedildi.", {
        description: `${ad} — görseller dahil, şablondan bağımsız.`,
      });
    } catch (e) {
      hataGoster(e);
    }
  }

  async function projeYukle(dosya: File | undefined) {
    if (!dosya) return;
    try {
      onProjeYukle(await projeOku(dosya, tip));
      toast.success("Proje yüklendi.", { description: dosya.name });
    } catch (e) {
      hataGoster(e);
    } finally {
      if (dosyaRef.current) dosyaRef.current.value = "";
    }
  }

  /* Odağı hata bölgesine taşı: kullanıcı sayfanın neresinde olursa olsun
     sorunu görür ve ekran okuyucu metni okur. Efekt, düğüm bağlandıktan
     sonra çalıştığı için ref burada kesinlikle hazırdır. */
  useEffect(() => {
    if (odakNo > 0) hataRef.current?.focus();
  }, [odakNo]);

  useEffect(() => {
    uretRef.current = uret;
    projeKaydetRef.current = projeKaydet;
  });

  useEffect(() => {
    function tus(e: KeyboardEvent) {
      const hedef = e.target;
      if (
        hedef instanceof HTMLInputElement ||
        hedef instanceof HTMLTextAreaElement ||
        (hedef instanceof HTMLElement && hedef.isContentEditable)
      ) {
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        void uretRef.current();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        projeKaydetRef.current();
      }
    }
    window.addEventListener("keydown", tus);
    return () => window.removeEventListener("keydown", tus);
  });

  return (
    <div className="sticky bottom-0 z-30 -mx-4 border-t border-border bg-background/85 px-4 py-2.5 backdrop-blur supports-[backdrop-filter]:bg-background/70 sm:-mx-6 sm:px-6">
      <AnimatePresence initial={false}>
        {hata && (
          <motion.div
            key="uretim-hatasi"
            ref={hataRef}
            role="alert"
            tabIndex={-1}
            initial={azHareket ? { opacity: 0 } : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={azHareket ? { opacity: 0 } : { opacity: 0, y: 8 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto mb-2 flex max-w-[1600px] items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive outline-none focus-visible:ring-2 focus-visible:ring-destructive"
          >
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span className="flex-1">{hata}</span>
            <button
              type="button"
              onClick={() => setHata(null)}
              aria-label="Hata uyarısını kapat"
              className="shrink-0 rounded p-0.5 transition-colors hover:bg-destructive/15"
            >
              <X className="size-4" aria-hidden />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-2">
        <Button
          onClick={uret}
          disabled={uretiliyor}
          aria-busy={uretiliyor}
          size="sm"
          className="min-w-44 bg-accent text-accent-foreground hover:bg-accent/90"
        >
          {uretiliyor ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Üretiliyor…
            </>
          ) : (
            <>
              <Download className="size-4" aria-hidden />
              Excel Dosyası Üret
            </>
          )}
        </Button>

        <Button onClick={sablon} disabled={sablonIniyor} size="sm" variant="outline">
          {sablonIniyor ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : (
            <FileDown className="size-4" aria-hidden />
          )}
          Boş Şablon
        </Button>

        <Separator orientation="vertical" className="mx-1 hidden h-6 sm:block" />

        <Button onClick={projeKaydet} size="sm" variant="outline">
          <Save className="size-4" aria-hidden />
          Projeyi Kaydet
        </Button>

        <Button
          onClick={() => dosyaRef.current?.click()}
          size="sm"
          variant="outline"
        >
          <FolderOpen className="size-4" aria-hidden />
          Proje Yükle
        </Button>
        <input
          ref={dosyaRef}
          type="file"
          accept=".json,application/json"
          className="sr-only"
          onChange={(e) => void projeYukle(e.target.files?.[0])}
          aria-label="Proje dosyası yükle"
        />

        <Button
          onClick={() => {
            setHata(null);
            onSifirla();
          }}
          size="sm"
          variant="ghost"
          className="text-muted-foreground"
        >
          <RotateCcw className="size-4" aria-hidden />
          Temizle
        </Button>

        {durum && (
          <span
            className="ml-auto font-mono text-xs tabular-nums text-muted-foreground"
            aria-live="polite"
          >
            {durum}
            <span className="hidden lg:inline"> · Ctrl+Enter üret · Ctrl+S kaydet</span>
          </span>
        )}
      </div>
    </div>
  );
}
