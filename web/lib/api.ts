import type { IsgIkon } from "./types";
import { oturumDustu } from "./oturum";

/** Motorun döndürdüğü anlaşılır Türkçe hata. Teknik iz ASLA taşınmaz. */
export class MotorHatasi extends Error {
  /** Kullanıcıya gösterilecek Türkçe metin (message ile aynı, okunurluk için). */
  readonly mesaj: string;

  constructor(mesaj: string, readonly detay?: string) {
    super(mesaj);
    this.name = "MotorHatasi";
    this.mesaj = mesaj;
  }
}

async function hataCoz(yanit: Response): Promise<never> {
  /* Oturum düştüyse arayüz giriş ekranına döner. Aksi halde kullanıcı, asıl
     sorun oturum zaman aşımıyken "dosya üretilemedi" gibi yanıltıcı bir
     mesajla baş başa kalır ve ne yapacağını bilemez. */
  if (yanit.status === 401) oturumDustu();

  let mesaj = "Dosya üretilemedi.";
  let detay: string | undefined;
  try {
    const govde = await yanit.json();
    if (typeof govde?.hata === "string") mesaj = govde.hata;
    if (typeof govde?.detay === "string" && govde.detay) detay = govde.detay;
  } catch {
    /* JSON değilse varsayılan mesaj kalır */
  }
  throw new MotorHatasi(mesaj, detay);
}

/** İçerik-Disposition başlığından dosya adını çıkarır. */
function dosyaAdiCoz(yanit: Response, varsayilan: string): string {
  const bas = yanit.headers.get("Content-Disposition") ?? "";
  return /filename="?([^"]+)"?/.exec(bas)?.[1] ?? varsayilan;
}

/** Üretilen dosyayı indirir. Blob URL her durumda serbest bırakılır. */
function indirmeyiBaslat(blob: Blob, dosyaAdi: string): void {
  const adres = URL.createObjectURL(blob);
  try {
    const baglanti = document.createElement("a");
    baglanti.href = adres;
    baglanti.download = dosyaAdi;
    baglanti.rel = "noopener";
    document.body.appendChild(baglanti);
    baglanti.click();
    baglanti.remove();
  } finally {
    // Chrome indirmeyi kuyruğa aldıktan sonra serbest bırakmak güvenli.
    setTimeout(() => URL.revokeObjectURL(adres), 10_000);
  }
}

async function agHatasi(e: unknown): Promise<never> {
  if (e instanceof MotorHatasi) throw e;
  throw new MotorHatasi(
    "Excel motoruna ulaşılamadı. Motorun çalıştığından emin olun " +
      "(python -m uvicorn ui.app:app --port 8000).",
  );
}

/** Belge üretir ve indirir; üretilen dosyanın adını döndürür. */
export async function belgeUret(
  yol: string,
  govde: unknown,
  varsayilanAd = "dokuman.xlsx",
): Promise<string> {
  let yanit: Response;
  try {
    yanit = await fetch(yol, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(govde),
    });
  } catch (e) {
    return agHatasi(e);
  }
  if (!yanit.ok) await hataCoz(yanit);

  const dosyaAdi = dosyaAdiCoz(yanit, varsayilanAd);
  indirmeyiBaslat(await yanit.blob(), dosyaAdi);
  return dosyaAdi;
}

/** Boş şablonu indirir. */
export async function bosSablonIndir(tip: string): Promise<string> {
  let yanit: Response;
  try {
    yanit = await fetch(`/api/bos/${tip}`);
  } catch (e) {
    return agHatasi(e);
  }
  if (!yanit.ok) await hataCoz(yanit);

  const dosyaAdi = dosyaAdiCoz(yanit, `bos_${tip}.xlsx`);
  indirmeyiBaslat(await yanit.blob(), dosyaAdi);
  return dosyaAdi;
}

export async function isgIkonlariniGetir(): Promise<IsgIkon[]> {
  try {
    const yanit = await fetch("/api/isg-ikonlari");
    if (!yanit.ok) await hataCoz(yanit);
    return (await yanit.json()).ikonlar ?? [];
  } catch (e) {
    return agHatasi(e);
  }
}

export async function unvanlariGetir(): Promise<string[]> {
  try {
    const yanit = await fetch("/api/ayarlar/unvanlar");
    if (!yanit.ok) await hataCoz(yanit);
    return (await yanit.json()).normal_unvanlar ?? [];
  } catch (e) {
    return agHatasi(e);
  }
}

export async function unvanlariKaydet(unvanlar: string[]): Promise<string[]> {
  try {
    const yanit = await fetch("/api/ayarlar/unvanlar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ normal_unvanlar: unvanlar }),
    });
    if (!yanit.ok) await hataCoz(yanit);
    return (await yanit.json()).normal_unvanlar ?? [];
  } catch (e) {
    return agHatasi(e);
  }
}

export interface BicimKurali {
  ad: string;
  alan: string;
  operator: string;
  degerler: string[];
  bicim: { kalin: boolean; renk: string; italik: boolean };
  etkin: boolean;
}

export async function kurallariGetir(): Promise<{
  varsayilan: { kalin: boolean; renk: string; italik: boolean };
  kurallar: BicimKurali[];
}> {
  try {
    const yanit = await fetch("/api/ayarlar/kurallar");
    if (!yanit.ok) await hataCoz(yanit);
    return await yanit.json();
  } catch (e) {
    return agHatasi(e);
  }
}

export async function kurallariKaydet(govde: {
  varsayilan: { kalin: boolean; renk: string; italik: boolean };
  kurallar: BicimKurali[];
}): Promise<void> {
  try {
    const yanit = await fetch("/api/ayarlar/kurallar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(govde),
    });
    if (!yanit.ok) await hataCoz(yanit);
  } catch (e) {
    return agHatasi(e);
  }
}

export interface IceAktarmaSonucu {
  ad_soyad: string;
  unvan: string;
  calisma_yeri: string;
  telefon: string;
  durak: string;
}

export async function personelIceAktar(
  dosyaAdi: string,
  icerik: string,
): Promise<IceAktarmaSonucu[]> {
  try {
    const yanit = await fetch("/api/vardiya/ice-aktar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dosya_adi: dosyaAdi, icerik }),
    });
    if (!yanit.ok) await hataCoz(yanit);
    return (await yanit.json()).kayitlar ?? [];
  } catch (e) {
    return agHatasi(e);
  }
}
