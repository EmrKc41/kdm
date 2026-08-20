import type { NextConfig } from "next";

/* Excel motoru ayrı bir Python (FastAPI) sürecinde çalışır. İstekleri Next
   üzerinden yönlendiriyoruz: böylece tarayıcı tek origin görür, CORS ayarı
   gerekmez ve dağıtımda adres tek yerden değişir. */
const MOTOR = process.env.MOTOR_ADRESI ?? "http://127.0.0.1:8000";

/* Güvenlik başlıkları.

   Uygulama bir giriş ekranının arkasında ve oturum çerezi kullanıyor; bu
   başlıklar olmadan başka bir sayfa uygulamayı görünmez bir çerçeveye alıp
   giriş yapmış operatöre farkında olmadan tıklatabilir (clickjacking).

   CSP bilinçli olarak dar: uygulama internetsiz bir fabrika makinesinde
   çalışır, hiçbir dış kaynağa istek atmaz. Fontlar derleme sırasında
   indirilip kendi sunucumuzdan servis edilir, ikonlar paket içindedir.

   BİLİNEN SINIR: script-src 'unsafe-inline' içerir. Denendi ve kaldırıldığında
   üretim derlemesinde sayfa TAMAMEN BOŞ kalıyor — Next'in satır içi önyükleme
   betiği engellendiği için React hiç başlamıyor. Bunu kaldırmanın yolu, her
   istekte nonce üreten bir middleware kurmaktır; bu da statik ön derlemeyi
   kapatır. Uygulamada kullanıcı HTML'i render eden hiçbir yer olmadığı
   (dangerouslySetInnerHTML kullanılmıyor) ve arayüz yalnızca yerel makinede
   çalıştığı için bu ödünç kabul edildi. Değerlendirmeyi değiştiren şey,
   dışarıdan gelen metnin HTML olarak basılmaya başlaması olur. */
const GELISTIRME = process.env.NODE_ENV === "development";

/* Geliştirme modunun iki ek ihtiyacı var ve ikisi de ÜRETİME sızmamalı:
   React dev derlemesi hata ayıklama için eval() kullanır, Next ise sıcak
   yeniden yükleme için bir WebSocket açar. Üretim derlemesinde ikisi de
   gerekmez; bu yüzden izinler yalnızca geliştirmede verilir. */
const BETIK_KAYNAGI = GELISTIRME
  ? "'self' 'unsafe-inline' 'unsafe-eval'"
  : "'self' 'unsafe-inline'";
const BAGLANTI_KAYNAGI = GELISTIRME
  ? "'self' ws://localhost:* http://localhost:*"
  : "'self'";

const GUVENLIK_BASLIKLARI = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `script-src ${BETIK_KAYNAGI}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      `connect-src ${BAGLANTI_KAYNAGI}`,
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:yol*", destination: `${MOTOR}/api/:yol*` }];
  },
  async headers() {
    return [{ source: "/:yol*", headers: GUVENLIK_BASLIKLARI }];
  },
};

export default nextConfig;
