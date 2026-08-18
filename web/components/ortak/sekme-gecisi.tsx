"use client";

import { motion, useReducedMotion } from "motion/react";

/** Sekme paneli göründüğünde kısa bir yumuşama.

    Radix sekmeleri pasif paneli DOM'dan kaldırır; bu yüzden her geçiş yeni
    bir bağlanmadır ve giriş hareketi tek başına yeterlidir. Hareket bilinçli
    olarak küçük tutulur: form yoğun bir ekranda büyük kayma, kullanıcının
    baktığı alanı kaybettirir (ui-ux-pro-max: excessive-motion).

    Yalnızca opacity ve transform kullanılır — ikisi de GPU'da bileşiklenir,
    düzen yeniden hesaplanmaz. */
export function SekmeGecisi({ children }: { children: React.ReactNode }) {
  const azHareket = useReducedMotion();

  return (
    <motion.div
      initial={azHareket ? { opacity: 0 } : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}
