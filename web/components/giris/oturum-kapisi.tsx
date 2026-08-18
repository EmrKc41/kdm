"use client";

import { useEffect, useSyncExternalStore } from "react";
import { abone, acikMi, durumuTazele, kontrolBittiMi } from "@/lib/oturum";
import { Skeleton } from "@/components/ortak/iskelet";
import { GirisEkrani } from "./giris-ekrani";

/** Oturum açık değilse giriş ekranını, açıksa uygulamayı gösterir.
 *
 *  `children` sunucuda render edilip buraya prop olarak geçer; ana sayfa
 *  Sunucu Bileşeni kalmaya devam eder (Next.js: istemci bileşenlerini yaprağa it).
 *
 *  Karar motora aittir: açılışta `/api/oturum/durum` sorulur. İlk yanıt
 *  gelene kadar NE giriş ekranı NE uygulama gösterilir — aksi halde oturumu
 *  açık olan kullanıcı her yenilemede giriş ekranının bir an parlamasını
 *  görürdü. */
export function OturumKapisi({ children }: { children: React.ReactNode }) {
  const acik = useSyncExternalStore(abone, acikMi, () => false);
  const hazir = useSyncExternalStore(abone, kontrolBittiMi, () => false);

  useEffect(() => {
    void durumuTazele();
  }, []);

  if (!hazir) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-3" aria-busy aria-label="Oturum denetleniyor">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  return acik ? <>{children}</> : <GirisEkrani />;
}
