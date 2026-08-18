/** Oturum durumu.
 *
 * Kimlik doğrulama MOTORDA yapılır (`ui/guvenlik.py`). Buradaki kod yalnızca
 * motorun verdiği yanıtı yansıtır; kendi başına bir karar vermez. Jeton
 * HttpOnly çerezde durur, bu yüzden bu dosya jetonu hiç görmez ve saklamaz.
 */

/** Motorun oturumu tanıyıp tanımadığı; yalnızca arayüzü doğru ekrana
 *  yönlendirmek için tutulur, yetki kararı değildir. */
let acik = false;
let ilkKontrolBitti = false;

const dinleyiciler = new Set<() => void>();

function duyur(): void {
  dinleyiciler.forEach((d) => d());
}

export class OturumHatasi extends Error {
  constructor(readonly mesaj: string) {
    super(mesaj);
    this.name = "OturumHatasi";
  }
}

export function acikMi(): boolean {
  return acik;
}

export function kontrolBittiMi(): boolean {
  return ilkKontrolBitti;
}

/** Sayfa açılışında motorun oturumu tanıyıp tanımadığını sorar. */
export async function durumuTazele(): Promise<void> {
  try {
    const yanit = await fetch("/api/oturum/durum", { cache: "no-store" });
    acik = yanit.ok && (await yanit.json()).acik === true;
  } catch {
    // Motor kapalıysa oturum da yok sayılır; giriş ekranı motor durumunu
    // zaten ayrıca gösterir.
    acik = false;
  }
  ilkKontrolBitti = true;
  duyur();
}

export async function girisYap(kullanici: string, parola: string): Promise<void> {
  let yanit: Response;
  try {
    yanit = await fetch("/api/oturum/giris", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kullanici, parola }),
    });
  } catch {
    throw new OturumHatasi(
      "Excel motoruna ulaşılamadı. Motorun çalıştığından emin olun.",
    );
  }

  if (!yanit.ok) {
    let mesaj = "Kullanıcı adı veya parola hatalı.";
    try {
      const govde = await yanit.json();
      if (typeof govde?.hata === "string") mesaj = govde.hata;
    } catch {
      /* JSON değilse varsayılan mesaj kalır */
    }
    throw new OturumHatasi(mesaj);
  }

  acik = true;
  duyur();
}

export async function cikisYap(): Promise<void> {
  try {
    await fetch("/api/oturum/cikis", { method: "POST" });
  } finally {
    acik = false;
    duyur();
  }
}

/** Motor 401 döndüğünde arayüzü giriş ekranına düşürür. Böylece oturum
 *  zaman aşımına uğradığında kullanıcı anlamsız hata mesajları yerine
 *  doğrudan giriş ekranını görür. */
export function oturumDustu(): void {
  if (!acik) return;
  acik = false;
  duyur();
}

export function abone(geri: () => void): () => void {
  dinleyiciler.add(geri);
  return () => {
    dinleyiciler.delete(geri);
  };
}
