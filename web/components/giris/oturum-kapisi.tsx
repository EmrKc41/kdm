"use client";

import { useSyncExternalStore } from "react";
import { SUNUCU_DURUMU, abone, acikMi } from "@/lib/oturum";
import { GirisEkrani } from "./giris-ekrani";

/** Oturum açık değilse giriş ekranını, açıksa uygulamayı gösterir.
 *
 *  `children` sunucuda render edilip buraya prop olarak geçer; bu sayede
 *  ana sayfa Sunucu Bileşeni kalmaya devam eder ve yalnızca kapı istemcide
 *  çalışır (Next.js kılavuzu: istemci bileşenlerini yaprağa it).
 *
 *  Durum useSyncExternalStore ile okunur: sunucu her zaman "kapalı" görür,
 *  istemci sessionStorage'dan okur. useEffect + setState ile yapılsaydı
 *  fazladan bir render turu oluşur ve ilk karede uygulama bir an görünürdü. */
export function OturumKapisi({ children }: { children: React.ReactNode }) {
  const acik = useSyncExternalStore(abone, acikMi, () => SUNUCU_DURUMU);
  return acik ? <>{children}</> : <GirisEkrani />;
}
