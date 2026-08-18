import {
  type Download,
  type Locator,
  type Page,
  expect,
  test as temelTest,
} from "@playwright/test";

/** Motorun kurduğu oturum çerezinin adı (ui/guvenlik.py ile aynı). */
export const OTURUM_CEREZI = "kdu_oturum";

/* Uygulama bir giriş kapısının arkasında. Akış testlerinin konusu giriş
   değil, formların davranışı; bu yüzden oturum sayfa açılmadan önce gerçek
   uç çağrılarak alınır.

   Arayüzden form doldurmak yerine API çağrılıyor: giriş ekranının kendisi
   giris.spec.ts'te sınanıyor, burada tekrarı her testi yavaşlatır ve giriş
   ekranındaki bir aksaklık ilgisiz otuz testi birden düşürürdü.

   `page.request` tarayıcı bağlamının çerez kavanozunu paylaşır, dolayısıyla
   motorun kurduğu HttpOnly çerez sonraki sayfa isteklerine kendiliğinden
   eklenir. */
export const test = temelTest.extend({
  page: async ({ page }, kullan) => {
    const yanit = await page.request.post("/api/oturum/giris", {
      data: { kullanici: "admin", parola: "admin" },
    });
    expect(yanit.ok(), "test oturumu açılamadı").toBeTruthy();
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
