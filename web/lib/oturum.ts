/** Basit oturum kilidi.
 *
 * DİKKAT — bu bir GÜVENLİK katmanı DEĞİLDİR, arayüz kilididir.
 * Kimlik doğrulama tamamen tarayıcıda yapılır; Excel motoru (:8000) hâlâ
 * kimlik sormadan yanıt verir ve doğrudan çağrılabilir. Amaç, ortak kullanılan
 * bir fabrika makinesinde uygulamanın yanlışlıkla açık bırakılmasını
 * zorlaştırmaktır. Gerçek koruma gerektiğinde doğrulama motora taşınmalıdır.
 */

const ANAHTAR = "kdu-oturum";

/** Şimdilik sabit kimlik bilgileri (kullanıcı isteği). */
const KULLANICI = "admin";
const PAROLA = "admin";

/** sessionStorage bilinçli tercih: sekme kapanınca oturum düşer, böylece
 *  vardiya değişiminde makine başında açık kalmış oturum devralınmaz. */
function depo(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    // Gizli sekme veya kısıtlı tarayıcı ayarı
    return null;
  }
}

const dinleyiciler = new Set<() => void>();

function duyur(): void {
  dinleyiciler.forEach((d) => d());
}

export function acikMi(): boolean {
  return depo()?.getItem(ANAHTAR) === "acik";
}

export function girisYap(kullanici: string, parola: string): boolean {
  /* Kullanıcı adı ASCII olduğu için DEĞİŞMEZ küçültme kullanılır.
     toLocaleLowerCase("tr") burada yanlış olurdu: Türkçe kuralıyla
     "ADMIN" → "admın" (noktasız ı) olur ve doğru kimlik reddedilir.
     Türkçe küçültme yalnızca kullanıcı METNİ için doğrudur, sabit
     tanımlayıcılar için değil. */
  if (kullanici.trim().toLowerCase() !== KULLANICI || parola !== PAROLA) {
    return false;
  }
  depo()?.setItem(ANAHTAR, "acik");
  duyur();
  return true;
}

export function cikisYap(): void {
  depo()?.removeItem(ANAHTAR);
  duyur();
}

/** useSyncExternalStore için abonelik. Aynı sekmedeki değişimler `duyur` ile,
 *  başka sekmedekiler `storage` olayıyla gelir. */
export function abone(geri: () => void): () => void {
  dinleyiciler.add(geri);
  window.addEventListener("storage", geri);
  return () => {
    dinleyiciler.delete(geri);
    window.removeEventListener("storage", geri);
  };
}

/** Sunucuda oturum bilinemez; ilk render HER ZAMAN "kapalı" varsayar.
 *  Aksi halde sunucu ve istemci farklı ağaç üretir ve hydration uyuşmazlığı
 *  oluşur (bu projede daha önce yaşandı). */
export const SUNUCU_DURUMU = false;
