"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { motion, useReducedMotion } from "motion/react";
import { AlertCircle, LogIn } from "lucide-react";
import { OturumHatasi, girisYap } from "@/lib/oturum";
import { Alan } from "@/components/ortak/alan";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/* Hareket, tasarım sistemindeki "Data-Dense Dashboard" tonuna uygun biçimde
   ölçülü tutulur: logo ve kart kısa bir yükselişle gelir, alanlar kademeli
   açılır. Süreler 200-400 ms bandında; daha uzunu her açılışta bekletir ve
   günde onlarca kez giriş yapan operatörü yorar. */
const KAP = {
  gizli: {},
  goster: { transition: { staggerChildren: 0.07, delayChildren: 0.08 } },
};

export function GirisEkrani() {
  const azHareket = useReducedMotion();
  const [kullanici, setKullanici] = useState("");
  const [parola, setParola] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const [deneniyor, setDeneniyor] = useState(false);
  const kullaniciRef = useRef<HTMLInputElement>(null);

  /* autoFocus niteliği burada güvenilir değil: alan, giriş animasyonuyla
     birlikte bağlanıyor ve odak body'de kalıyordu. Operatör giriş ekranını
     açar açmaz yazmaya başlayabilmeli. */
  useEffect(() => {
    kullaniciRef.current?.focus();
  }, []);

  /* Azaltılmış hareket isteyen kullanıcı için yalnızca opacity; kayma yok. */
  const oge = {
    gizli: azHareket ? { opacity: 0 } : { opacity: 0, y: 12 },
    goster: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] as const },
    },
  };

  async function gonder(e: React.FormEvent) {
    e.preventDefault();
    setDeneniyor(true);
    setHata(null);
    try {
      await girisYap(kullanici, parola);
      // Başarıda kapı bileşeni yeniden render eder; burada durum sıfırlanmaz.
      return;
    } catch (hata) {
      // Mesaj motordan gelir; hangi alanın yanlış olduğunu bilerek söylemez.
      setHata(
        hata instanceof OturumHatasi ? hata.mesaj : "Giriş yapılamadı.",
      );
      setParola("");
      kullaniciRef.current?.focus();
    } finally {
      setDeneniyor(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-4 py-10">
      <motion.div
        variants={KAP}
        initial="gizli"
        animate="goster"
        className="w-full max-w-sm"
      >
        <motion.div variants={oge} className="mb-6 flex flex-col items-center text-center">
          <Image
            src="/marka/logo-192.png"
            alt=""
            width={72}
            height={72}
            priority
            aria-hidden
            className="mb-3 size-18 rounded-xl bg-white p-1 shadow-sm ring-1 ring-border"
          />
          <h1 className="text-lg font-bold tracking-tight">Kalite Doküman Üretici</h1>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Şablona sadık Excel çıktısı
          </p>
        </motion.div>

        <motion.form
          variants={oge}
          onSubmit={(e) => void gonder(e)}
          className="space-y-4 rounded-xl border border-border bg-card p-6 shadow-sm"
        >
          <motion.div variants={oge}>
            <Alan etiket="Kullanıcı Adı" htmlFor="g-kullanici">
              <Input
                id="g-kullanici"
                ref={kullaniciRef}
                value={kullanici}
                onChange={(e) => setKullanici(e.target.value)}
                autoComplete="username"
                required
              />
            </Alan>
          </motion.div>

          <motion.div variants={oge}>
            <Alan etiket="Parola" htmlFor="g-parola">
              <Input
                id="g-parola"
                type="password"
                value={parola}
                onChange={(e) => setParola(e.target.value)}
                autoComplete="current-password"
                required
              />
            </Alan>
          </motion.div>

          {hata && (
            <motion.div
              role="alert"
              initial={azHareket ? { opacity: 0 } : { opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18 }}
              className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
              {hata}
            </motion.div>
          )}

          <motion.div variants={oge}>
            <Button type="submit" disabled={deneniyor} className="w-full">
              <LogIn className="size-4" aria-hidden />
              Giriş Yap
            </Button>
          </motion.div>
        </motion.form>

        <motion.p
          variants={oge}
          className="mt-4 text-center text-[11px] leading-relaxed text-muted-foreground"
        >
          Bu giriş yalnızca arayüzü kilitler; belge motorunu korumaz.
        </motion.p>
      </motion.div>
    </div>
  );
}
