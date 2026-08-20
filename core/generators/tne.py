"""FONKSİYON 2 — Tek Nokta Eğitimi üreticisi (referans: taslaktne.xlsx).

ÖNEMLİ YAPISAL BULGU
    "EĞİTİM İÇERİĞİ" ve "EĞİTİM TÜRÜ" onay kutuları HÜCRE DOLGUSU DEĞİLDİR.
    drawing1.xml içinde yaşayan küçük dikdörtgen çizim nesneleridir; işaretli
    olanın dolgusu 00B050 (yeşil), işaretsiz olanınki noFill'dir. Bu yüzden
    işaretleme hücrelere değil, çizim katmanına yazılır.

KAPSAM KARARI
    Arayüz kullanıcıdan yalnızca şu alanları ister:
        eğitim içeriği · eğitim türü · eğitim süresi · sorumlu ·
        eğitim veren · tarih · parça (eğitim) resmi
    Kalan alanlar — müdürlük, kısım, hazırlayan, parametre, ölçüm aracı,
    TND no, katılımcı listesi — sahada personel tarafından KALEMLE
    doldurulur; bu yüzden boş bırakılır. Üretici bu alanları yine de
    doldurabilir (proje dosyası veya API üzerinden gelirse yazılır), ancak
    arayüz onları sormaz.
"""

from __future__ import annotations

from pathlib import Path

from .. import imaging, textutil
from ..errors import GirdiHatasi, SablonHatasi
from ..models import TneVerisi
from ..ooxml.drawing import Anchor, DrawingPart, make_picture_anchor
from ..ooxml.layout import SheetLayout
from ..ooxml.package import XlsxPackage
from ..ooxml.sheet import SheetPart, paylasilan_metinler
from ..ooxml.styles import StylePatcher
from ..units import TNE_IMAGE_HEIGHT_EMU, TNE_IMAGE_WIDTH_EMU

SHEET_PART = "xl/worksheets/sheet1.xml"
DRAWING_PART = "xl/drawings/drawing1.xml"
DRAWING_RELS = "xl/drawings/_rels/drawing1.xml.rels"

# --- Doğrulanmış hücre haritası ---------------------------------------------

BASLIK_HUCRESI = "B2"                 # B2:H5 birleşik
KONU_HUCRESI = "C7"                   # C7:E7 birleşik

#: Şablonda I2:J5 TEK BLOK DEĞİLDİR — dört ayrı satır birleşimidir ve her
#: hücre etiketi ile değeri birlikte tutar ("SAYFA NO      : 1/1").
DOKUMAN_BLOGU = {
    "sayfa_no": "I2",
    "talimat_no": "I3",
    "rev_no": "I4",
    "tarih": "I5",
}

#: Etiket ve değerin AYNI hücrede tutulduğu alanlar.
ETIKETLI_ALANLAR = {
    "mudurluk_birim": "B8",           # B8:C8 birleşik
    "kisim": "B9",
    "hazirlayan": "B10",
    "egitim_tarihi": "J7",
}

#: Etiketi ayrı hücrede olan, değeri kendi hücresine yazılan alanlar.
DEGER_HUCRELERI = {
    "parametre": "G7",
    "olcum_araci": "G8",
    "parca_etkisi": "G9",
    "sorumlu": "G10",
    "egitim_suresi": "I7",
    "tnd_no": "I8",                   # I8:J8 birleşik
    "egitim_veren": "I9",             # I9:J9 birleşik
}

# --- Katılımcı listesi -------------------------------------------------------

KATILIMCI_ILK_SATIR = 11
KATILIMCI_SON_SATIR = 42
KATILIMCI_AD_SUTUNU = "H"
KATILIMCI_SICIL_SUTUNU = "I"
# İMZA sütunu (J) bilinçli olarak BOŞ bırakılır — ıslak imza için.

MAKS_KATILIMCI = KATILIMCI_SON_SATIR - KATILIMCI_ILK_SATIR + 1   # 32

# --- Eğitim görseli alanı (B11:G42) -----------------------------------------

GORSEL_ILK_SUTUN = 1          # B
GORSEL_SON_SUTUN = 6          # G
GORSEL_ILK_SATIR = 10         # satır 11
GORSEL_SON_SATIR = 41         # satır 42

# --- Onay kutusu seçenekleri -------------------------------------------------

EGITIM_ICERIGI = ["GÜVENLİK", "ÜRETİM", "KALİTE", "BAKIM", "STANDART", "ÇEVRE"]
EGITIM_TURU = ["TEMEL BİLGİ", "İYİLEŞTİRME", "HATA"]

ISARETLI_RENK = "00B050"      # şablondaki yeşil

# --- Puntolar ----------------------------------------------------------------
# 2.2: şablonda başlık 36 punto; talep gereği 24 punto uygulanır.

PUNTO_BASLIK = 24
PUNTO_KONU = 14
PUNTO_DEGER = 10


def uret(veri: TneVerisi, sablon: str | Path) -> XlsxPackage:
    """Doldurulmuş bir Tek Nokta Eğitimi paketi üretir."""
    _dogrula(veri)

    pkg = XlsxPackage.open(sablon)
    sst = paylasilan_metinler(pkg.read_text("xl/sharedStrings.xml"))
    sheet = SheetPart(pkg.read_text(SHEET_PART), sst)
    styles = StylePatcher(pkg.read_text("xl/styles.xml"))
    drawing = DrawingPart(pkg.read_text(DRAWING_PART))
    layout = SheetLayout(sheet.xml)

    _yaz_baslik_ve_konu(sheet, styles, veri)
    _yaz_alanlar(sheet, styles, veri)
    _yaz_dokuman_blogu(sheet, veri)
    _yaz_katilimcilar(sheet, styles, veri)

    _isaretle_onay_kutulari(drawing, veri)
    _yerlestir_logo(pkg, drawing, veri)
    _yerlestir_egitim_gorseli(pkg, drawing, layout, veri)

    pkg.write_text(SHEET_PART, sheet.xml)
    pkg.write_text("xl/styles.xml", styles.to_xml())
    pkg.write_text(DRAWING_PART, drawing.to_xml())
    return pkg


def bos_sablon(sablon: str | Path) -> XlsxPackage:
    """Hiç veri girilmemiş şablon kopyası (2.8)."""
    return XlsxPackage.open(sablon)


# --- Hücre yazımı ------------------------------------------------------------


def _yaz_baslik_ve_konu(
    sheet: SheetPart, styles: StylePatcher, veri: TneVerisi
) -> None:
    if veri.baslik.strip():
        # Şablonda 36 punto; talep gereği 24 punto sabittir.
        stil = styles.derive(sheet.style_of(BASLIK_HUCRESI), size=PUNTO_BASLIK)
        sheet.set_text(BASLIK_HUCRESI, veri.baslik.strip(), style=stil)

    konu = veri.konu_metni
    if konu:
        stil = styles.derive(sheet.style_of(KONU_HUCRESI), size=PUNTO_KONU)
        sheet.set_text(KONU_HUCRESI, konu, style=stil)


def _yaz_alanlar(sheet: SheetPart, styles: StylePatcher, veri: TneVerisi) -> None:
    for alan, hucre in ETIKETLI_ALANLAR.items():
        deger = str(getattr(veri, alan) or "").strip()
        if deger:
            stil = styles.derive(sheet.style_of(hucre), size=PUNTO_DEGER)
            sheet.etiketi_koruyarak_yaz(hucre, deger, style=stil)

    for alan, hucre in DEGER_HUCRELERI.items():
        deger = str(getattr(veri, alan) or "").strip()
        if deger:
            stil = styles.derive(sheet.style_of(hucre), size=PUNTO_DEGER)
            sheet.set_text(hucre, deger, style=stil)


def _yaz_dokuman_blogu(sheet: SheetPart, veri: TneVerisi) -> None:
    """I2:I5 bloğu — etiketin hizalama boşlukları korunur."""
    for alan, hucre in DOKUMAN_BLOGU.items():
        deger = str(getattr(veri, alan) or "").strip()
        if deger:
            sheet.etiketi_koruyarak_yaz(hucre, deger)


def _yaz_katilimcilar(
    sheet: SheetPart, styles: StylePatcher, veri: TneVerisi
) -> None:
    """2.7 — Eğitimi alanları önceden yazar; İMZA sütunu boş kalır."""
    for i, kisi in enumerate(veri.katilimcilar):
        satir = KATILIMCI_ILK_SATIR + i
        if kisi.ad_soyad.strip():
            hucre = f"{KATILIMCI_AD_SUTUNU}{satir}"
            stil = styles.derive(sheet.style_of(hucre), size=PUNTO_DEGER)
            sheet.set_text(hucre, kisi.ad_soyad.strip(), style=stil)
        if kisi.sicil_no.strip():
            hucre = f"{KATILIMCI_SICIL_SUTUNU}{satir}"
            stil = styles.derive(sheet.style_of(hucre), size=PUNTO_DEGER)
            sheet.set_text(hucre, kisi.sicil_no.strip(), style=stil)


# --- Onay kutuları -----------------------------------------------------------


def onay_kutulari(drawing: DrawingPart) -> dict[str, Anchor]:
    """Etiket metinlerini kendi onay kutusu dikdörtgeniyle eşleştirir.

    Eşleştirme GEOMETRİK yapılır: her etiket metin kutusunun solundaki, aynı
    satırdaki en yakın boş dikdörtgen onun onay kutusudur. Şekil kimliklerine
    sabit kodlanmaz, çünkü şablondaki adlar tekil değildir ("14 Dikdörtgen"
    üç kez geçer).
    """
    sekiller = drawing.find_all_shapes()
    etiketler = [a for a in sekiller if a.text.strip()]
    kutular = [a for a in sekiller if not a.text.strip()]

    eslesme: dict[str, Anchor] = {}
    for etiket in etiketler:
        ad = etiket.text.strip()
        if ad not in EGITIM_ICERIGI and ad not in EGITIM_TURU:
            continue

        _, _, e_satir, _ = etiket.from_marker
        e_x, _ = etiket.offset

        adaylar = [
            k
            for k in kutular
            if k.from_marker[2] == e_satir and k.offset[0] < e_x
        ]
        if adaylar:
            eslesme[ad] = max(adaylar, key=lambda k: k.offset[0])
    return eslesme


def _isaretle_onay_kutulari(drawing: DrawingPart, veri: TneVerisi) -> None:
    """2.5 — Seçilenler yeşil dolgu alır, seçilmeyenler boşaltılır."""
    kutular = onay_kutulari(drawing)

    eksik = (set(EGITIM_ICERIGI) | set(EGITIM_TURU)) - set(kutular)
    if eksik:
        raise SablonHatasi(
            "Şablondaki onay kutuları tanınamadı: " + ", ".join(sorted(eksik))
        )

    secili = {s.strip() for s in veri.egitim_icerigi} | {
        s.strip() for s in veri.egitim_turu
    }
    for ad, kutu in kutular.items():
        kutu.set_fill(ISARETLI_RENK if ad in secili else None)


# --- Görseller ---------------------------------------------------------------


def _gorsel_degistir(
    pkg: XlsxPackage, rid: str, gorsel: bytes, cx: int, cy: int
) -> None:
    """Mevcut medya parçasının üzerine, uzantısına UYGUN biçimde yazar.

    TNE şablonunun logosu .jpeg'dir. Oraya PNG baytı yazmak dosya içeriğini
    [Content_Types] bildirimiyle çelişkiye düşürürdü.
    """
    import re

    rels = pkg.read_text(DRAWING_RELS)
    m = re.search(rf'<Relationship[^>]*Id="{rid}"[^>]*Target="([^"]+)"', rels)
    if not m:
        raise SablonHatasi(f"Şablonda {rid} görsel ilişkisi bulunamadı.")

    hedef = m.group(1).replace("../", "xl/").lstrip("/")
    bicim = imaging.bicim_sec(hedef)
    pkg.write_bytes(hedef, imaging.hazirla(gorsel, cx, cy, bicim=bicim))


def _yerlestir_logo(
    pkg: XlsxPackage, drawing: DrawingPart, veri: TneVerisi
) -> None:
    """Logoyu değiştirir; ÖLÇÜ ŞABLONDAN DEVRALINIR.

    Faz 0 kararı: TNE şablonunun logosu 6,76 x 3,43 cm'dir ve İş Talimatı'ndaki
    1,55 x 3,28 cm ölçüsünden farklıdır. Her doküman kendi şablonuna sadık
    kalsın diye buradaki ölçü korunur.
    """
    if not veri.logo:
        return

    eski = next((a for a in drawing.find_pictures() if a.name == "Resim 19"), None)
    if eski is None:
        gorseller = drawing.find_pictures()
        if not gorseller:
            raise SablonHatasi("Şablonda logo görseli bulunamadı.")
        eski = gorseller[0]

    rid = eski.blip_rid
    if rid is None:
        raise SablonHatasi("Logo görselinin bağlantısı okunamadı.")

    cx, cy = eski.ext or (2432628, 1233632)
    _gorsel_degistir(pkg, rid, veri.logo, cx, cy)

    col, col_off, row, row_off = eski.from_marker
    yer = drawing.index_of(eski)
    drawing.remove(eski)
    drawing.insert(
        yer,
        make_picture_anchor(
            rid=rid,
            shape_id=eski.shape_id,
            name="Kurum Logosu",
            col=col,
            col_off=col_off,
            row=row,
            row_off=row_off,
            cx=cx,
            cy=cy,
        ),
    )


def _yerlestir_egitim_gorseli(
    pkg: XlsxPackage,
    drawing: DrawingPart,
    layout: SheetLayout,
    veri: TneVerisi,
) -> None:
    """B11:G42 alanına TAM 41,75 x 23,72 cm ölçüsünde yerleştirir.

    Ölçü sabittir (kullanıcı talebi): görselin oranı ne olursa olsun çıktıdaki
    kutu her zaman aynı boyuttadır. Görsel bu kutuyu TAMAMEN doldurur; oranı
    korunur ve taşan kenarlar ortadan kırpılır (bkz. core/imaging.py).
    `oneCellAnchor` kullanılır çünkü ölçü yalnızca bu anchor tipinde
    bağlayıcıdır.
    """
    if not veri.egitim_gorseli:
        return

    alan_y = layout.rows_emu(GORSEL_ILK_SATIR, GORSEL_SON_SATIR)
    cx, cy = TNE_IMAGE_WIDTH_EMU, TNE_IMAGE_HEIGHT_EMU

    islenmis = imaging.hazirla(veri.egitim_gorseli, cx, cy)
    ad = pkg.next_media_name("png")
    pkg.write_bytes(ad, islenmis)
    pkg.ensure_content_type_default("png", "image/png")

    from ..ooxml.drawing import PIC_REL_TYPE

    rid = pkg.add_relationship(DRAWING_RELS, ad, PIC_REL_TYPE)

    col, col_off = layout.center_offset(GORSEL_ILK_SUTUN, GORSEL_SON_SUTUN, cx)
    row_off = max(0, (alan_y - cy) // 2)
    row, row_off = _coz_ofset(layout.row_emu, GORSEL_ILK_SATIR, row_off)

    anchor = make_picture_anchor(
        rid=rid,
        shape_id=drawing.next_shape_id(),
        name="Egitim Gorseli",
        col=col,
        col_off=col_off,
        row=row,
        row_off=row_off,
        cx=cx,
        cy=cy,
    )
    # Arkaya gönder: listenin başına alınır, tüm onay kutularının arkasında kalır.
    drawing.insert(0, anchor)


def _coz_ofset(olcu, baslangic: int, mesafe: int) -> tuple[int, int]:
    i, kalan = baslangic, mesafe
    while True:
        w = olcu(i)
        if kalan < w or w <= 0:
            return i, int(kalan)
        kalan -= w
        i += 1


# --- Girdi doğrulaması -------------------------------------------------------


def _dogrula(veri: TneVerisi) -> None:
    # Başlık ZORUNLU DEĞİLDİR: şablon "TEK NOKTA EĞİTİMİ" başlığıyla gelir ve
    # kullanıcıdan yalnızca eğitime özgü alanlar istenir (bkz. modül başlığı).
    if len(veri.katilimcilar) > MAKS_KATILIMCI:
        raise GirdiHatasi(
            f"Katılımcı listesi en fazla {MAKS_KATILIMCI} kişi alabilir "
            f"({len(veri.katilimcilar)} kişi girildi). "
            "Fazla kişiler için ikinci bir form üretin."
        )

    for ad in veri.egitim_icerigi:
        if ad.strip() not in EGITIM_ICERIGI:
            raise GirdiHatasi(
                f"'{ad}' geçerli bir eğitim içeriği değil. "
                "Seçenekler: " + ", ".join(EGITIM_ICERIGI)
            )
    for ad in veri.egitim_turu:
        if ad.strip() not in EGITIM_TURU:
            raise GirdiHatasi(
                f"'{ad}' geçerli bir eğitim türü değil. "
                "Seçenekler: " + ", ".join(EGITIM_TURU)
            )
