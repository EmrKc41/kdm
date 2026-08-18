import {
  type Download,
  type Locator,
  type Page,
  expect,
  test as temelTest,
} from "@playwright/test";

/** Oturum anahtarı — lib/oturum.ts ile aynı olmalı. */
export const OTURUM_ANAHTARI = "kdu-oturum";

/* Uygulama bir giriş kapısının arkasında. Akış testlerinin ilgilendiği şey
   giriş değil, formların davranışı; bu yüzden oturum sayfa yüklenmeden önce
   açılmış sayılır. Giriş ekranının kendisi giris.spec.ts'te sınanır.

   addInitScript kullanılır çünkü storageState yalnızca localStorage taşır;
   oturum bilinçli olarak sessionStorage'da tutuluyor (sekme kapanınca düşsün). */
export const test = temelTest.extend({
  page: async ({ page }, kullan) => {
    await page.addInitScript((anahtar) => {
      sessionStorage.setItem(anahtar, "acik");
    }, OTURUM_ANAHTARI);
    await kullan(page);
  },
});

export { expect };

/** Dosya adı biçimi: "<KONU>_<DOKUMAN_TIPI>_GG.AA.YYYY.xlsx" (core/naming.py). */
export function adKalibi(dokuman: string): RegExp {
  return new RegExp(String.raw`${dokuman}_\d{2}\.\d{2}\.\d{4}\.xlsx$`);
}

/** İSG ve TNE kutuları sr-only'dir; tıklama komşu ikona takılır. Kullanıcı
    zaten etiketin kendisine bastığı için etiketi tıklamak doğru davranıştır. */
export async function kutuSec(kapsam: Locator, deger: string): Promise<Locator> {
  const kutu = kapsam.getByRole("checkbox", { name: deger });
  await kapsam.locator(`label:has(input[value="${deger}"])`).click();
  await expect(kutu).toBeChecked();
  return kutu;
}

export async function sekmeAc(page: Page, ad: string): Promise<void> {
  await page.goto("/");
  if (ad !== "İş Talimatı") await page.getByRole("tab", { name: ad }).click();
  // Motor hazır olmadan üretmek testleri sahte biçimde düşürür. Durum
  // metni görünür yazı değil, rozetin aria-label'ıdır (MotorDurumu).
  // Süre bilerek uzun: bu bir hazırlık beklemesi, testin konusu değil.
  // Paralel koşuda Next dev sunucusu sayfayı ilk kez derlerken varsayılan
  // 5 sn'ye sığmıyor ve testler sahte biçimde düşüyordu.
  await expect(
    page.getByRole("status", { name: /Excel motoru çalışıyor/ }),
  ).toBeVisible({ timeout: 20_000 });
}

/** "Excel Dosyası Üret"e basar ve inen dosyayı döndürür. */
export async function uret(page: Page): Promise<Download> {
  const inecek = page.waitForEvent("download");
  await page.getByRole("button", { name: "Excel Dosyası Üret" }).click();
  return inecek;
}

/** Üretimi dener ama dosya beklemez; doğrulama hatası bekleyen testler için. */
export async function uretDene(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Excel Dosyası Üret" }).click();
}
