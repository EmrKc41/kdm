import { ggaayyyy } from "@/lib/tarih";
import type { RaporVerisi } from "@/lib/types";
import { DurumPili } from "./durum-pili";

/** Excel çıktısındaki kurumsal bant renkleri — tema değil, kağıt sadakati. */
const BASLIK = "#1F3864";
const BANT = "#2E5395";
const ALTERNATIF = "#EEF2F8";
const KENAR = "#BFC9DA";

interface Ozellikler {
  veri: RaporVerisi;
}

export function RaporOnizleme({ veri }: Ozellikler) {
  const doluSatirlar = veri.satirlar.filter(
    (s) => s.tanim.trim() || s.kok_neden.trim() || s.duzeltici_faaliyet.trim(),
  );
  const gosterilecek =
    doluSatirlar.length > 0
      ? doluSatirlar.slice(0, 4)
      : veri.satirlar.slice(0, 2);

  const meta = [
    veri.konu.trim() && `Konu: ${veri.konu.trim()}`,
    veri.rapor_no.trim() && `Rapor No: ${veri.rapor_no.trim()}`,
    veri.tarih && `Tarih: ${ggaayyyy(veri.tarih) || veri.tarih}`,
    veri.hazirlayan.trim() && `Hazırlayan: ${veri.hazirlayan.trim()}`,
    veri.genel_durum && `Durum: ${veri.genel_durum}`,
  ]
    .filter(Boolean)
    .join("   ·   ");

  return (
    <div
      className="overflow-hidden rounded-md border text-[11px] leading-snug"
      style={{ borderColor: KENAR }}
      aria-label="Excel çıktı önizlemesi"
    >
      <div
        className="px-3 py-2 text-center text-xs font-bold text-white"
        style={{ backgroundColor: BASLIK }}
      >
        {veri.baslik.trim() || "KALİTE UYGUNSUZLUK TAKİP RAPORU"}
      </div>

      {meta && (
        <div
          className="flex flex-wrap gap-x-3 gap-y-1 px-3 py-1.5 text-[10px] font-semibold text-white"
          style={{ backgroundColor: BANT }}
        >
          {meta}
          {veri.genel_durum && (
            <DurumPili durum={veri.genel_durum} className="ml-auto shrink-0" />
          )}
        </div>
      )}

      <div className="border-b px-3 py-2" style={{ borderColor: KENAR, backgroundColor: ALTERNATIF }}>
        <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-600">Özet</p>
        <p className="whitespace-pre-wrap text-slate-800">
          {veri.ozet.trim() || (
            <span className="italic text-slate-400">Özet metni burada görünür…</span>
          )}
        </p>
      </div>

      <div className="overflow-x-auto kaydirma-ince">
        <table className="w-full min-w-[640px] border-collapse">
          <thead>
            <tr style={{ backgroundColor: BASLIK, color: "#fff" }}>
              {["#", "Tanım", "Kök Neden", "Düzeltici", "Sorumlu", "Durum"].map((h) => (
                <th key={h} className="border px-2 py-1.5 text-left text-[10px] font-bold" style={{ borderColor: KENAR }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gosterilecek.map((satir, i) => {
              const bos =
                !satir.tanim.trim() &&
                !satir.kok_neden.trim() &&
                !satir.duzeltici_faaliyet.trim();
              return (
                <tr
                  key={satir.id}
                  style={{
                    backgroundColor: i % 2 === 1 ? ALTERNATIF : "#fff",
                  }}
                >
                  <td className="border px-2 py-1.5 font-mono text-slate-500" style={{ borderColor: KENAR }}>
                    {i + 1}
                  </td>
                  <td className="border px-2 py-1.5" style={{ borderColor: KENAR }}>
                    {bos ? (
                      <span className="italic text-slate-400">—</span>
                    ) : (
                      satir.tanim.trim() || "…"
                    )}
                  </td>
                  <td className="border px-2 py-1.5 text-slate-700" style={{ borderColor: KENAR }}>
                    {satir.kok_neden.trim() || "—"}
                  </td>
                  <td className="border px-2 py-1.5 text-slate-700" style={{ borderColor: KENAR }}>
                    {satir.duzeltici_faaliyet.trim() || "—"}
                  </td>
                  <td className="border px-2 py-1.5" style={{ borderColor: KENAR }}>
                    {satir.sorumlu.trim() || "—"}
                  </td>
                  <td className="border px-2 py-1.5" style={{ borderColor: KENAR }}>
                    <DurumPili durum={satir.durum || "Açık"} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {doluSatirlar.length > 4 && (
        <p className="px-3 py-1.5 text-[10px] text-muted-foreground">
          +{doluSatirlar.length - 4} satır daha (Excel&apos;de tamamı yazılır)
        </p>
      )}
    </div>
  );
}
