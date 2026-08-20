import {
  SABLONLAR_VAR, adKalibi, expect, kutuSec, sekmeAc, test, uret, uretDene,
} from "./yardimcilar";

test.describe("İş Talimatı akışı", () => {
  test("talimat adı boşken üretim engellenir", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await uretDene(page);
    await expect(page.getByText("Talimat adı zorunludur.")).toBeVisible();
  });

  test("konu önizlemesi otomatik eki gösterir ve kutu kaldırılınca kaybolur", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Konu / Parça Referansı").fill("10598-AG");
    await expect(page.getByText("10598-AG İŞ TALİMATI HK.")).toBeVisible();

    await page.getByRole("checkbox", { name: /İŞ TALİMATI HK\." ekle/ }).click();
    await expect(page.getByText("10598-AG İŞ TALİMATI HK.")).toHaveCount(0);
  });

  test("dolu adım sayacı doldurdukça artar", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await expect(page.getByText("0 / 9 dolu")).toBeVisible();

    await page.getByLabel("Sarı Alan Başlığı").first().fill("MARKALAMA");
    await expect(page.getByText("1 / 9 dolu")).toBeVisible();

    await page.getByRole("button", { name: "Temizle" }).first().click();
    await expect(page.getByText("0 / 9 dolu")).toBeVisible();
  });

  test("sarı alan sınırı aşılırsa metin sessizce kırpılmaz, üretim durur", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Talimat Adı").fill("FIREWALL İŞ TALİMATI");
    await page.getByLabel("Sarı Alan Açıklaması").first().fill("A".repeat(260));
    await uretDene(page);
    await expect(page.getByText(/sınırını aşıyor/)).toBeVisible();
  });

  test("İSG ekipmanı seçilebilir", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await kutuSec(page.getByRole("group", { name: "İSG ekipmanı seçimi" }), "baret");
  });

  test("talimat üretilir ve dosya adı kurala uyar", async ({ page }) => {
  test.skip(!SABLONLAR_VAR, "templates/ altında şablon yok (depoda tutulmuyor)");
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Talimat Adı").fill("FIREWALL İŞ TALİMATI");
    await page.getByLabel("Konu / Parça Referansı").fill("10598-AG");
    await page.getByLabel("Sarı Alan Başlığı").first().fill("MARKALAMA");
    await page.getByLabel("Cycle Süresi (saniye)").first().fill("3");

    const inen = await uret(page);
    expect(inen.suggestedFilename()).toMatch(adKalibi("IS_TALIMATI"));
    await expect(page.getByText("Dosya indirildi.")).toBeVisible();
  });

  test("adım sırası sürüklemeden, düğmeyle de değiştirilebilir", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    const basliklar = page.getByLabel("Sarı Alan Başlığı");
    await basliklar.first().fill("BİRİNCİ");

    // WCAG 2.2: sürükleme tek yol olamaz.
    await expect(page.getByRole("button", { name: "1. adımı yukarı taşı" })).toBeDisabled();
    await page.getByRole("button", { name: "1. adımı aşağı taşı" }).click();

    await expect(basliklar.nth(0)).toHaveValue("");
    await expect(basliklar.nth(1)).toHaveValue("BİRİNCİ");
  });

  test("doğrulama hatası odaklanabilir bir uyarıda duyurulur", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await uretDene(page);

    // Next.js kendi rota duyurucusunu da role="alert" ile eklediği için
    // arama sekme paneline daraltılır.
    const uyari = page.getByRole("tabpanel").getByRole("alert");
    await expect(uyari).toContainText("Talimat adı zorunludur.");
    await expect(uyari).toBeFocused();

    await page.getByRole("button", { name: "Hata uyarısını kapat" }).click();
    await expect(uyari).toHaveCount(0);
  });
});
