import { adKalibi, expect, sekmeAc, test, uret, uretDene } from "./yardimcilar";

test.describe("Kalite Raporu akışı", () => {
  test("konu boşken üretim engellenir", async ({ page }) => {
    await sekmeAc(page, "Kalite Raporu");
    await uretDene(page);
    await expect(page.getByText("Konu / parça referansı zorunludur.")).toBeVisible();
  });

  test("uygunsuzluk satırı eklenir ve durum seçilebilir", async ({ page }) => {
    await sekmeAc(page, "Kalite Raporu");
    await page.getByRole("button", { name: "Satır Ekle" }).click();

    await page.getByLabel("1. satır Uygunsuzluk Tanımı").fill("KAYNAK ÇAPAĞI");
    await page.getByLabel("1. satır Sorumlu").fill("KALİTE");

    await page.getByLabel("1. satır Durum").click();
    await page.getByRole("option", { name: "Devam Ediyor" }).click();
    await expect(page.getByLabel("1. satır Durum")).toContainText("Devam Ediyor");
  });

  test("rapor üretilir ve dosya adı kurala uyar", async ({ page }) => {
    await sekmeAc(page, "Kalite Raporu");
    await page.getByLabel("Konu / Parça *").fill("10598-AG");
    await page.getByLabel("Hazırlayan").fill("A. YILMAZ");
    await page.getByLabel("Özet").fill("Seri kontrolde çapak tespit edildi.");

    const inen = await uret(page);
    expect(inen.suggestedFilename()).toMatch(adKalibi("KALITE_RAPORU"));
    await expect(page.getByText("Dosya indirildi.")).toBeVisible();
  });
});
