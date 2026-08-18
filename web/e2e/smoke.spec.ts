import { expect, test } from "./yardimcilar";

test.describe("Ana sayfa kabuk testleri", () => {
  test("başlık ve sekmeler görünür", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Kalite Doküman Üretici" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "İş Talimatı" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Tek Nokta Eğitimi" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Vardiya Listesi" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Kalite Raporu" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Ayarlar" })).toBeVisible();
  });

  test("kalite raporu sekmesi formu açılır", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Kalite Raporu" }).click();
    await expect(page.getByText("Rapor Kimliği")).toBeVisible();
    await expect(page.getByRole("button", { name: "Excel Dosyası Üret" })).toBeVisible();
  });

  test("konu boşken üretim engellenir", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Kalite Raporu" }).click();
    await page.getByRole("button", { name: "Excel Dosyası Üret" }).click();
    await expect(page.getByText("Konu / parça referansı zorunludur.")).toBeVisible();
  });
});
