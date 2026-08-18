import { expect, test } from "@playwright/test";
import { OTURUM_ANAHTARI } from "./yardimcilar";

/* Bu dosya BİLEREK temel `test`i kullanır: diğer spec'lerdeki oturum
   fixture'ı sayfayı açık oturumla yükler ve giriş ekranını hiç göstermez. */

test.describe("Giriş ekranı", () => {
  test("oturum yokken uygulama gösterilmez", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Giriş Yap" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toHaveCount(0);
  });

  test("yanlış parola reddedilir ve hangi alanın hatalı olduğu söylenmez", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Kullanıcı Adı").fill("admin");
    await page.getByLabel("Parola").fill("yanlis");
    await page.getByRole("button", { name: "Giriş Yap" }).click();

    // Next.js rota duyurucusu da role="alert" taşır; arama forma daraltılır.
    const uyari = page.locator("form").getByRole("alert");
    await expect(uyari).toContainText("Kullanıcı adı veya parola hatalı.");
    // Parola alanı temizlenir; uygulama hâlâ kilitli.
    await expect(page.getByLabel("Parola")).toHaveValue("");
    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toHaveCount(0);
  });

  test("doğru kimlikle uygulama açılır", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Kullanıcı Adı").fill("admin");
    await page.getByLabel("Parola").fill("admin");
    await page.getByRole("button", { name: "Giriş Yap" }).click();

    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Oturumu kapat" })).toBeVisible();
  });

  test("kullanıcı adı büyük harfle de kabul edilir", async ({ page }) => {
    await page.goto("/");
    // Türkçe küçültme kuralı burada YANLIŞ olurdu: "ADMIN" → "admın".
    // Bu test o regresyonu tutar.
    await page.getByLabel("Kullanıcı Adı").fill("ADMIN");
    await page.getByLabel("Parola").fill("admin");
    await page.getByRole("button", { name: "Giriş Yap" }).click();

    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toBeVisible();
  });

  test("çıkış yapınca uygulama tekrar kilitlenir", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Kullanıcı Adı").fill("admin");
    await page.getByLabel("Parola").fill("admin");
    await page.getByRole("button", { name: "Giriş Yap" }).click();
    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toBeVisible();

    await page.getByRole("button", { name: "Oturumu kapat" }).click();
    await expect(page.getByRole("button", { name: "Giriş Yap" })).toBeVisible();
    await expect(
      page.evaluate((a) => sessionStorage.getItem(a), OTURUM_ANAHTARI),
    ).resolves.toBeNull();
  });

  test("oturum sekme oturumuyla sınırlıdır, kalıcı depoya yazılmaz", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Kullanıcı Adı").fill("admin");
    await page.getByLabel("Parola").fill("admin");
    await page.getByRole("button", { name: "Giriş Yap" }).click();
    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toBeVisible();

    // localStorage'a yazılsaydı oturum tarayıcı kapansa da açık kalırdı.
    await expect(
      page.evaluate((a) => localStorage.getItem(a), OTURUM_ANAHTARI),
    ).resolves.toBeNull();
  });
});
