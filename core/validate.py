"""Çıktı doğrulayıcı — üretilen her dosya diske yazılmadan ÖNCE çalışır.

Program hiçbir koşulda sessizce bozuk dosya üretmez. Bir bulgu varsa
`DogrulamaHatasi` fırlatılır ve dosya yazılmaz.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import DogrulamaHatasi
from .ooxml.drawing import DrawingPart
from .ooxml.package import XlsxPackage

#: Kaybolmaması gereken, openpyxl'in tipik olarak sildiği parçalar.
KORUNMASI_GEREKEN_DESENLER = (
    "xl/printerSettings/",
    "customXml/",
    "docMetadata/",
)

#: Baytı baytına aynı kalması gereken sayfa/baskı ayarları.
SAYFA_AYARI_ETIKETLERI = ("pageSetup", "pageMargins", "printOptions")


def dogrula(
    uretilen: XlsxPackage,
    sablon_yolu: str | Path,
    *,
    sheet_part: str = "xl/worksheets/sheet1.xml",
    drawing_part: str = "xl/drawings/drawing1.xml",
    beklenen_metinler: list[str] | None = None,
    beklenen_gorsel_olculeri: list[tuple[str, int, int]] | None = None,
    metin_kutusu_silindi: int = 0,
    gorsel_silindi: int = 0,
) -> list[str]:
    """Üretilen paketi şablonla karşılaştırır. Bulgu listesi boşsa dosya temizdir.

    Bulgu varsa `DogrulamaHatasi` fırlatır.
    """
    sablon = XlsxPackage.open(sablon_yolu)
    bulgular: list[str] = []

    bulgular += _parca_kontrolu(sablon, uretilen)
    bulgular += _sayfa_ayari_kontrolu(sablon, uretilen, sheet_part)
    bulgular += _birlesik_hucre_kontrolu(sablon, uretilen, sheet_part)
    bulgular += _cizim_kontrolu(
        sablon, uretilen, drawing_part, metin_kutusu_silindi, gorsel_silindi
    )
    bulgular += _z_sirasi_kontrolu(uretilen, drawing_part)
    bulgular += _xml_saglik_kontrolu(uretilen)

    if beklenen_metinler:
        bulgular += _metin_kontrolu(uretilen, drawing_part, beklenen_metinler)
    if beklenen_gorsel_olculeri:
        bulgular += _olcu_kontrolu(uretilen, drawing_part, beklenen_gorsel_olculeri)

    if bulgular:
        raise DogrulamaHatasi(
            "Üretilen dosya şablon sadakat denetimini geçemedi, "
            "bu yüzden kaydedilmedi.",
            bulgular,
        )
    return bulgular


# --- Tekil denetimler --------------------------------------------------------


def _parca_kontrolu(sablon: XlsxPackage, uretilen: XlsxPackage) -> list[str]:
    kayip = set(sablon.names()) - set(uretilen.names())
    bulgular = []
    for ad in sorted(kayip):
        if any(ad.startswith(d) for d in KORUNMASI_GEREKEN_DESENLER):
            bulgular.append(f"Kritik parça kayboldu: {ad}")
        else:
            bulgular.append(f"Şablon parçası kayboldu: {ad}")
    return bulgular


def _sayfa_ayari_kontrolu(
    sablon: XlsxPackage, uretilen: XlsxPackage, sheet_part: str
) -> list[str]:
    a, b = sablon.read_text(sheet_part), uretilen.read_text(sheet_part)
    bulgular = []
    for etiket in SAYFA_AYARI_ETIKETLERI:
        ma = re.search(rf"<{etiket}\b[^>]*/?>", a)
        mb = re.search(rf"<{etiket}\b[^>]*/?>", b)
        if (ma.group(0) if ma else None) != (mb.group(0) if mb else None):
            bulgular.append(
                f"Baskı ayarı değişmiş <{etiket}>: "
                f"şablon={ma.group(0) if ma else 'yok'} / "
                f"çıktı={mb.group(0) if mb else 'yok'}"
            )
    return bulgular


def _birlesik_hucre_kontrolu(
    sablon: XlsxPackage, uretilen: XlsxPackage, sheet_part: str
) -> list[str]:
    def merges(pkg: XlsxPackage) -> set[str]:
        return set(re.findall(r'<mergeCell ref="([^"]+)"', pkg.read_text(sheet_part)))

    a, b = merges(sablon), merges(uretilen)
    bulgular = []
    if a - b:
        bulgular.append(f"Birleşik hücre kayboldu: {sorted(a - b)}")
    if b - a:
        bulgular.append(f"Şablonda olmayan birleşik hücre eklenmiş: {sorted(b - a)}")
    return bulgular


def _cizim_kontrolu(
    sablon: XlsxPackage,
    uretilen: XlsxPackage,
    drawing_part: str,
    silinen: int,
    gorsel_silindi: int = 0,
) -> list[str]:
    if not sablon.has(drawing_part):
        return []
    if not uretilen.has(drawing_part):
        return ["Çizim katmanı (drawing1.xml) tamamen kaybolmuş."]

    d_a = DrawingPart(sablon.read_text(drawing_part))
    d_b = DrawingPart(uretilen.read_text(drawing_part))

    sp_a = len(d_a.find_all_shapes())
    sp_b = len(d_b.find_all_shapes())
    beklenen = sp_a - silinen

    bulgular = []
    if sp_b < beklenen:
        bulgular.append(
            f"Metin kutusu kaybı: şablonda {sp_a}, çıktıda {sp_b} adet "
            f"(beklenen en az {beklenen}). Kullanıcının silmediği kutular yok olmuş."
        )

    # Şablondaki her metin kutusunun karşılığı çıktıda var mı?
    if silinen == 0:
        adlar_a = sorted(a.name for a in d_a.find_all_shapes())
        adlar_b = sorted(a.name for a in d_b.find_all_shapes())
        for ad in adlar_a:
            if adlar_b.count(ad) < adlar_a.count(ad):
                bulgular.append(f"Şablondaki '{ad}' çizim nesnesi çıktıda eksik.")
                break

    pic_a, pic_b = len(d_a.find_pictures()), len(d_b.find_pictures())
    if pic_b < pic_a - gorsel_silindi:
        bulgular.append(
            f"Görsel kaybı: şablonda {pic_a}, çıktıda {pic_b} adet "
            f"(beklenen en az {pic_a - gorsel_silindi})."
        )
    return bulgular


def _z_sirasi_kontrolu(uretilen: XlsxPackage, drawing_part: str) -> list[str]:
    """Kontrol adımı görselleri tüm metin kutularının arkasında olmalı."""
    if not uretilen.has(drawing_part):
        return []
    d = DrawingPart(uretilen.read_text(drawing_part))

    ilk_sp = next(
        (i for i, a in enumerate(d.anchors) if a.shape_kind == "sp"), None
    )
    if ilk_sp is None:
        return []

    bulgular = []
    for i, a in enumerate(d.anchors):
        if a.shape_kind == "pic" and "Kontrol Adimi" in a.name and i > ilk_sp:
            bulgular.append(
                f"Z-sırası hatası: '{a.name}' metin kutularının ÜSTÜNDE kalıyor "
                f"(konum {i}, ilk metin kutusu {ilk_sp}). Arkaya gönderilmeli."
            )
    return bulgular


def _metin_kontrolu(
    uretilen: XlsxPackage, drawing_part: str, beklenen: list[str]
) -> list[str]:
    d = DrawingPart(uretilen.read_text(drawing_part))
    mevcut = [a.text.strip() for a in d.find_all_shapes()]
    return [
        f"Beklenen metin kutusu yazısı çıktıda yok: '{m}'"
        for m in beklenen
        if m.strip() not in mevcut
    ]


def _olcu_kontrolu(
    uretilen: XlsxPackage,
    drawing_part: str,
    beklenen: list[tuple[str, int, int]],
) -> list[str]:
    """Görsel ölçülerini EMU cinsinden TAM eşitlik ile denetler."""
    d = DrawingPart(uretilen.read_text(drawing_part))
    bulgular = []
    for ad, cx, cy in beklenen:
        anchor = next((a for a in d.anchors if a.name == ad), None)
        if anchor is None:
            bulgular.append(f"Beklenen görsel çıktıda yok: '{ad}'")
            continue
        m = re.search(r'<xdr:ext cx="(\d+)" cy="(\d+)"/>', anchor.xml)
        if not m:
            bulgular.append(f"'{ad}' görselinin ölçüsü okunamadı.")
            continue
        gercek = (int(m.group(1)), int(m.group(2)))
        if gercek != (cx, cy):
            bulgular.append(
                f"'{ad}' ölçüsü yanlış: beklenen {cx}x{cy} EMU, "
                f"bulunan {gercek[0]}x{gercek[1]} EMU."
            )
    return bulgular


def _xml_saglik_kontrolu(uretilen: XlsxPackage) -> list[str]:
    """Değiştirilen XML parçalarının hâlâ ayrıştırılabilir olduğunu doğrular."""
    from xml.etree import ElementTree as ET

    bulgular = []
    for ad in uretilen.names():
        if not ad.endswith(".xml") and not ad.endswith(".rels"):
            continue
        try:
            ET.fromstring(uretilen.read_bytes(ad))
        except ET.ParseError as exc:
            bulgular.append(f"Bozuk XML üretildi ({ad}): {exc}")
    return bulgular
