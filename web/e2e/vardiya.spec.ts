import { adKalibi, expect, sekmeAc, test, uret } from "./yardimcilar";

test.describe("Vardiya Listesi akışı", () => {
  test("vardiya anahtarı A/B/C arasında geçiş yapar", async ({ page }) => {
    await sekmeAc(page, "Vardiya Listesi");
    const vardiyalar = page.getByRole("tablist", { name: "Vardiya seçimi" });

    // Varsayılan gündüz vardiyasıdır (B); form B ile açılır.
    await expect(vardiyalar.getByRole("tab", { name: /B VARDİYASI/ })).toHaveAttribute(
      "aria-selected", "true",
    );
    await vardiyalar.getByRole("tab", { name: /C VARDİYASI/ }).click();
    await expect(vardiyalar.getByRole("tab", { name: /C VARDİYASI/ })).toHaveAttribute(
      "aria-selected", "true",
    );
    await expect(page.getByText("C Vardiyası Personel Listesi")).toBeVisible();
  });

  test("satır eklenip silinebilir ve kayıt sayacı güncellenir", async ({ page }) => {
    await sekmeAc(page, "Vardiya Listesi");
    await page.getByRole("button", { name: "Satır Ekle" }).first().click();

    await page.getByLabel("1. satır Ad Soyad").fill("MEHMET DEMİR");
    await expect(
      page.getByRole("tab", { name: /B VARDİYASI/ }).getByText("1 kayıt"),
    ).toBeVisible();

    await page.getByRole("button", { name: "1. satırı sil" }).click();
    await expect(page.getByLabel("1. satır Ad Soyad")).toHaveValue("");
  });

  test("vardiya listesi üretilir ve dosya adı kurala uyar", async ({ page }) => {
    await sekmeAc(page, "Vardiya Listesi");
    await page.getByLabel("1. satır Ad Soyad").fill("MEHMET DEMİR");
    await page.getByLabel("1. satır Ünvan").fill("OPERATÖR");
    await page.getByLabel("1. satır Telefon No").fill("05001112233");

    const inen = await uret(page);
    expect(inen.suggestedFilename()).toMatch(adKalibi("VARDIYA_LISTESI"));
    await expect(page.getByText("Dosya indirildi.")).toBeVisible();
  });
});
