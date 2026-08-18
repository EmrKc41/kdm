import { adKalibi, expect, kutuSec, sekmeAc, test, uret } from "./yardimcilar";

test.describe("Tek Nokta Eğitimi akışı", () => {
  test("eğitim içeriği ve türü seçimi sayaca yansır", async ({ page }) => {
    await sekmeAc(page, "Tek Nokta Eğitimi");
    await expect(page.getByText("0 seçim")).toBeVisible();

    await kutuSec(page.getByRole("group", { name: "Eğitim içeriği" }), "KALİTE");
    await kutuSec(page.getByRole("group", { name: "Eğitim türü" }), "TEMEL BİLGİ");

    await expect(page.getByText("2 seçim")).toBeVisible();
  });

  test("sahada elle doldurulacak alanlar arayüzde sorulmaz", async ({ page }) => {
    await sekmeAc(page, "Tek Nokta Eğitimi");
    await expect(page.getByText("Sahada Elle Doldurulacak Alanlar")).toBeVisible();
  });

  test("TNE üretilir ve dosya adı kurala uyar", async ({ page }) => {
    await sekmeAc(page, "Tek Nokta Eğitimi");
    await kutuSec(page.getByRole("group", { name: "Eğitim içeriği" }), "GÜVENLİK");
    await page.getByLabel("Eğitim Süresi").fill("15 DK");
    await page.getByLabel("Sorumlu").fill("A. YILMAZ");

    const inen = await uret(page);
    expect(inen.suggestedFilename()).toMatch(adKalibi("TEK_NOKTA_EGITIMI"));
    await expect(page.getByText("Dosya indirildi.")).toBeVisible();
  });
});
