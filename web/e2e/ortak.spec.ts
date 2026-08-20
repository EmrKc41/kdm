import path from "node:path";
import { SABLONLAR_VAR, expect, sekmeAc, test } from "./yardimcilar";

test.describe("Ortak eylemler", () => {
  test("motor durumu şablonların hazır olduğunu bildirir", async ({ page }) => {
  test.skip(!SABLONLAR_VAR, "templates/ altında şablon yok (depoda tutulmuyor)");
    await page.goto("/");
    await expect(
      page.getByRole("status", { name: "Excel motoru çalışıyor · şablonlar hazır" }),
    ).toBeVisible();
  });

  test("boş şablon indirilir", async ({ page }) => {
  test.skip(!SABLONLAR_VAR, "templates/ altında şablon yok (depoda tutulmuyor)");
    await sekmeAc(page, "İş Talimatı");
    const inecek = page.waitForEvent("download");
    await page.getByRole("button", { name: "Boş Şablon" }).click();
    const inen = await inecek;
    expect(inen.suggestedFilename()).toMatch(/^BOS_IS_TALIMATI_.*\.xlsx$/);
  });

  test("proje kaydedilip geri yüklendiğinde form aynı kalır", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Talimat Adı").fill("KAYNAK İŞ TALİMATI");
    await page.getByLabel("Parça No").fill("77-ABC");

    const inecek = page.waitForEvent("download");
    await page.getByRole("button", { name: "Projeyi Kaydet" }).click();
    const proje = await inecek;
    expect(proje.suggestedFilename()).toMatch(/\.json$/);
    const yol = path.join(test.info().outputDir, proje.suggestedFilename());
    await proje.saveAs(yol);

    await page.getByRole("button", { name: "Temizle" }).last().click();
    await expect(page.getByLabel("Talimat Adı")).toHaveValue("");

    await page.getByLabel("Proje dosyası yükle").setInputFiles(yol);
    await expect(page.getByLabel("Talimat Adı")).toHaveValue("KAYNAK İŞ TALİMATI");
    await expect(page.getByLabel("Parça No")).toHaveValue("77-ABC");
  });

  test("Ctrl+Enter kısayolu üretimi tetikler", async ({ page }) => {
  test.skip(!SABLONLAR_VAR, "templates/ altında şablon yok (depoda tutulmuyor)");
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Talimat Adı").fill("KISAYOL TALİMATI");
    await page.getByRole("heading", { name: "Kalite Doküman Merkezi" }).click();

    const inecek = page.waitForEvent("download");
    await page.keyboard.press("Control+Enter");
    const inen = await inecek;
    expect(inen.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test("tema düğmesi koyu temaya ulaşır", async ({ page }) => {
    await page.goto("/");
    const dugme = page.getByRole("button", { name: /tema/i });

    /* Döngü: sistem → açık → koyu. Sistem teması zaten açıkken ilk basış
       renkleri değiştirmez (ikon ve etiket değişir) — bu beklenen davranış.
       Anlamlı olan, düğmeyi çevirerek koyu temaya ULAŞILABİLMESİ ve kök
       öğeye "dark" sınıfının gerçekten uygulanması. */
    for (let i = 0; i < 3; i++) {
      const etiket = (await dugme.getAttribute("aria-label")) ?? "";
      if (etiket.includes("Koyu tema —")) break;
      await dugme.click();
    }

    await expect
      .poll(() => page.evaluate(() => document.documentElement.classList.contains("dark")))
      .toBe(true);
  });

  test("ayarlar sekmesi ünvan kurallarını gösterir", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Ayarlar" }).click();
    await expect(page.getByRole("button", { name: /Kaydet/ }).first()).toBeVisible();
  });
});

test.describe("Motor kapalıyken", () => {
  test("üretim hatası anlaşılır Türkçe mesaj verir", async ({ page }) => {
    await sekmeAc(page, "İş Talimatı");
    await page.getByLabel("Talimat Adı").fill("HATA TESTİ");
    // Motoru gerçekten durdurmak yerine isteği ağ katmanında kesiyoruz:
    // testler paralel koştuğu için sunucuyu kapatmak diğerlerini düşürürdü.
    await page.route("**/api/talimat", (yol) => yol.abort());

    await page.getByRole("button", { name: "Excel Dosyası Üret" }).click();
    await expect(page.getByText(/Excel motoruna ulaşılamadı/)).toBeVisible();
  });
});

test.describe("Güvenlik başlıkları", () => {
  test("sayfa clickjacking'e ve tür tahminine karşı korunur", async ({ page }) => {
    const yanit = await page.goto("/");
    const basliklar = yanit!.headers();

    // Uygulama oturum çerezi kullanıyor; çerçevelenebilirse giriş yapmış
    // operatör görünmez bir katmanda kandırılabilir.
    expect(basliklar["x-frame-options"]).toBe("DENY");
    expect(basliklar["content-security-policy"]).toContain("frame-ancestors 'none'");
    expect(basliklar["x-content-type-options"]).toBe("nosniff");
    expect(basliklar["referrer-policy"]).toBe("no-referrer");
  });

  test("üretim derlemesinde eval ve dış bağlantı açılmaz", async ({ page }) => {
    const yanit = await page.goto("/");
    const csp = yanit!.headers()["content-security-policy"] ?? "";

    // Geliştirmede React eval() ister, Next HMR soketi açar; bu izinlerin
    // üretime sızmadığını doğrulamak bu testin tek amacı.
    if (process.env.CI) {
      expect(csp).not.toContain("unsafe-eval");
      expect(csp).not.toContain("ws://");
    }
    expect(csp).toContain("object-src 'none'");
  });
});

