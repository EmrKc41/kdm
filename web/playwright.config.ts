import { defineConfig, devices } from "@playwright/test";

/* Arayüz testleri gerçek Excel motoruna karşı koşar: "üret" düğmesi bir
   xlsx indirir ve testler indirilen dosyanın adını doğrular. Bu yüzden
   Playwright iki sunucuyu birden ayağa kaldırır — yalnızca Next.js
   başlatmak, üretim akışlarını sessizce test dışı bırakır. */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  /* Yerelde işçi sayısı sınırlı: sekiz paralel istek soğuk bir Next dev
     sunucusunu aynı anda derlemeye zorluyor ve testler koda değil derleme
     kuyruğuna takılıp düşüyordu. CI zaten derlenmiş sürümü tek işçiyle koşar. */
  workers: process.env.CI ? 1 : 4,
  reporter: "list",
  /* Varsayılan 5 sn, Next dev sunucusu bir sayfayı ilk kez derlerken
     yetmiyor ve testler koda değil derleme gecikmesine takılıp düşüyordu. */
  expect: { timeout: 10_000 },
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Motor kök dizinden çalışır; templates/ ve ayarlar/ yolları oraya göredir.
      command: "python -m uvicorn ui.app:app --host 127.0.0.1 --port 8000 --log-level warning",
      cwd: "..",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      /* CI'da derlenmiş sürüm çalıştırılır: iş akışı zaten `npm run build`
         yapıyor, dolayısıyla dev sunucusunun istek anında derleme
         gecikmesini testlere taşımasının hiçbir faydası yok. Yerelde
         `npm run dev` kalır ki değişiklik anında görünsün. */
      command: process.env.CI ? "npm run start" : "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
