/* core/models.py karşılıkları. Alan adları Python tarafıyla BİREBİR aynıdır;
   arayüz ile motor arasında isim çevirisi yapılmaz. */

export type BosBlok = "cerceveli" | "temizle";

export interface KontrolAdimi {
  id: string;              // yalnızca istemci tarafı (sürükle-bırak kimliği)
  baslik: string;
  aciklama: string;
  cycle_sn: string;        // boş dizge = girilmedi
  gorsel: string | null;   // data URL
  gorselAdi: string;
}

export interface TalimatVerisi {
  baslik: string;
  baslik_buyuk_harf: boolean;
  konu: string;
  konu_otomatik_ek: boolean;
  parca_no: string;
  parca_adi: string;
  musteri: string;
  hazirlama_tarihi: string;
  hazirlayan: string;
  son_rev_tarihi: string;
  musteri_temsilcisi: string;
  son_rev_aciklamasi: string;
  onay: string;
  isg_ikonlari: string[];
  sayfa_no: string;
  talimat_no: string;
  rev_no: string;
  tarih: string;
  logo: string | null;
  bos_blok_davranisi: BosBlok;
  adimlar: KontrolAdimi[];
}

export interface TneVerisi {
  egitim_icerigi: string[];
  egitim_turu: string[];
  egitim_suresi: string;
  sorumlu: string;
  egitim_veren: string;
  egitim_tarihi: string;
  tarih: string;
  egitim_gorseli: string | null;
}

export interface VardiyaKaydi {
  id: string;
  ad_soyad: string;
  unvan: string;
  calisma_yeri: string;
  telefon: string;
  durak: string;
}

export type VardiyaHarfi = "A" | "B" | "C";

export interface VardiyaBlogu {
  vardiya_adi: VardiyaHarfi;
  vardiya_saati: string;
  kayitlar: VardiyaKaydi[];
}

export interface HaftalikVardiya {
  tarih: string;
  normal_unvanlar: string[];
  vardiyalar: VardiyaBlogu[];
}

export interface RaporSatiri {
  id: string;
  tanim: string;
  kok_neden: string;
  duzeltici_faaliyet: string;
  sorumlu: string;
  hedef_tarih: string;
  durum: string;
}

export interface RaporVerisi {
  baslik: string;
  konu: string;
  rapor_no: string;
  tarih: string;
  hazirlayan: string;
  genel_durum: string;
  ozet: string;
  satirlar: RaporSatiri[];
}

export interface IsgIkon {
  ad: string;
  etiket: string;
}

/* Sarı alan sınırı — core/generators/talimat.py ile aynı olmalıdır. */
export const SARI_ALAN_SINIRI = 250;

export const EGITIM_ICERIGI = [
  "GÜVENLİK", "ÜRETİM", "KALİTE", "BAKIM", "STANDART", "ÇEVRE",
] as const;

export const EGITIM_TURU = ["TEMEL BİLGİ", "İYİLEŞTİRME", "HATA"] as const;

export const VARDIYA_SAATLERI: Record<VardiyaHarfi, string> = {
  A: "24.00 - 08.00",
  B: "08.00 - 16.00",
  C: "16.00 - 24.00",
};
