/**
 * Proje dosyası (.json) okuma/yazma.
 *
 * Biçim, Python tarafındaki `core/models.py` ile AYNIDIR:
 *
 *     { "surum": 1, "tip": "talimat" | "tne" | "vardiya", "veri": { ... } }
 *
 * Görseller `veri` içinde data URL olarak durur; dosya tek başına taşınabilir,
 * şablonlara hiçbir bağı yoktur.
 */

export const PROJE_SURUMU = 1;

export type ProjeTipi = "talimat" | "tne" | "vardiya" | "rapor";

const TIP_ETIKETI: Record<ProjeTipi, string> = {
  talimat: "is_talimati",
  tne: "tek_nokta_egitimi",
  vardiya: "vardiya_listesi",
  rapor: "kalite_raporu",
};

export class ProjeHatasi extends Error {
  readonly mesaj: string;
  constructor(mesaj: string) {
    super(mesaj);
    this.name = "ProjeHatasi";
    this.mesaj = mesaj;
  }
}

/** Form durumunu .json olarak indirir; indirilen dosya adını döndürür. */
export function projeIndir(tip: ProjeTipi, veri: unknown): string {
  const govde = { surum: PROJE_SURUMU, tip, veri };
  const bugun = new Date().toISOString().slice(0, 10);
  const dosyaAdi = `proje_${TIP_ETIKETI[tip]}_${bugun}.json`;

  const blob = new Blob([JSON.stringify(govde, null, 2)], {
    type: "application/json;charset=utf-8",
  });
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
    setTimeout(() => URL.revokeObjectURL(adres), 10_000);
  }
  return dosyaAdi;
}

/**
 * Proje dosyasını okur ve doğrular.
 *
 * Tip uyuşmazlığı sessizce yutulmaz: TNE projesi vardiya sekmesine
 * yüklenmeye çalışılırsa anlaşılır bir hata verilir.
 */
export async function projeOku(
  dosya: File,
  beklenenTip: ProjeTipi,
): Promise<Record<string, unknown>> {
  let govde: unknown;
  try {
    govde = JSON.parse(await dosya.text());
  } catch {
    throw new ProjeHatasi(
      `"${dosya.name}" geçerli bir proje dosyası değil veya bozulmuş.`,
    );
  }

  if (typeof govde !== "object" || govde === null) {
    throw new ProjeHatasi(`"${dosya.name}" beklenen yapıda değil.`);
  }
  const p = govde as { surum?: unknown; tip?: unknown; veri?: unknown };

  if (p.surum !== PROJE_SURUMU) {
    throw new ProjeHatasi(
      `Proje dosyası bu sürümle uyumlu değil. Beklenen sürüm ${PROJE_SURUMU}, ` +
        `dosyadaki ${String(p.surum ?? "belirtilmemiş")}.`,
    );
  }
  if (p.tip !== beklenenTip) {
    const ad: Record<string, string> = {
      talimat: "İş Talimatı",
      tne: "Tek Nokta Eğitimi",
      vardiya: "Vardiya Listesi",
      rapor: "Kalite Raporu",
    };
    throw new ProjeHatasi(
      `Bu dosya bir "${ad[String(p.tip)] ?? p.tip}" projesi. ` +
        `${ad[beklenenTip]} sekmesine yüklenemez.`,
    );
  }
  if (typeof p.veri !== "object" || p.veri === null) {
    throw new ProjeHatasi("Proje dosyasında veri bölümü bulunamadı.");
  }

  return p.veri as Record<string, unknown>;
}
