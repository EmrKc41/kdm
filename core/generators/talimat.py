"""FONKSİYON 1 — İş Talimatı üreticisi (referans: taslaktalimat.xlsx).

Şablon sıfırdan çizilmez; kopyalanıp doldurulur. Tüm işlemler ZIP/XML
seviyesinde yapılır, böylece 10 adet metin kutusu, yazıcı ayarları ve
customXml parçaları eksiksiz korunur.
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import imaging, isg_ikonlari, textutil
from ..errors import GirdiHatasi, SablonHatasi
from ..models import TalimatVerisi
from ..ooxml.drawing import (
    PIC_REL_TYPE,
    DrawingPart,
    clone_textbox,
    make_picture_anchor,
)
from ..ooxml.layout import SheetLayout
from ..ooxml.package import XlsxPackage
from ..ooxml.sheet import Run, SheetPart
from ..ooxml.styles import StylePatcher
from ..units import (
    LOGO_HEIGHT_EMU,
    LOGO_WIDTH_EMU,
    STEP_IMAGE_HEIGHT_EMU,
    STEP_IMAGE_WIDTH_EMU,
)

SHEET_PART = "xl/worksheets/sheet1.xml"
DRAWING_PART = "xl/drawings/drawing1.xml"
DRAWING_RELS = "xl/drawings/_rels/drawing1.xml.rels"

# --- Doğrulanmış hücre haritası ---------------------------------------------

BASLIK_HUCRESI = "A1"                 # A1:U4 birleşik
KONU_HUCRESI = "C5"                   # C5:W5 birleşik

#: Şablonda V1:W4 BİRLEŞİK DEĞİLDİR — 8 ayrı hücredir ve değerler ": " önekli.
DOKUMAN_BLOGU = {
    "sayfa_no": "W1",
    "talimat_no": "W2",
    "rev_no": "W3",
    "tarih": "W4",
}

#: Etiket/değer çiftlerinin değer hücreleri.
DEGER_HUCRELERI = {
    "parca_no": "C6",
    "parca_adi": "C7",
    "musteri": "J6",
    "hazirlama_tarihi": "J7",
    "hazirlayan": "N6",
    "son_rev_tarihi": "N7",
    "musteri_temsilcisi": "R6",
    "son_rev_aciklamasi": "R7",
    "onay": "V6",
    "isg_ekipmani": "V7",
}

#: Kontrol adımı ızgarası. Sütunlar 0 tabanlı: A=0 ... W=22.
SUTUN_GRUPLARI = [(0, 8), (9, 15), (16, 22)]      # A:I, J:P, Q:W
BANT_SAYISI = 3
BANT_ILK_SATIR = 7                                 # satır 8 (0 tabanlı)
BANT_SON_SATIR = 18                                # satır 19
BANT_ADIMI = 13                                    # sonraki bant 13 satır aşağıda

#: Sarı açıklama hücreleri (satır 20, 33, 46).
SARI_SUTUNLAR = ["A", "J", "Q"]

# --- Görev tanımında sabitlenen puntolar ------------------------------------
# Şablondaki değerlerden farklı olanlar bilinçli olarak eziliyor (Faz 0 onayı).

PUNTO_BASLIK = 24        # şablon: 24  (aynı)
PUNTO_KONU = 12          # şablon: 22  -> talep gereği 12, sola hizalı
PUNTO_DEGER = 10         # şablon: 14  -> talep gereği 10
PUNTO_SARI = 14          # şablon: 12/16 -> talep gereği 14

RENK_BASLIK_KIRMIZI = "FF0000"
RENK_ACIKLAMA_SIYAH = "000000"

#: P sütununun sabit genişliği (Excel karakter birimi).
#: Şablon 27,7109375 ile geliyordu; baskıda milimetrik kaymaya yol açtığı için
#: kullanıcı talebiyle sabitlendi. Bu, sütun genişliklerine yapılan TEK
#: bilinçli müdahaledir; diğer tüm sütunlar şablondaki gibi kalır.
P_SUTUN_GENISLIGI = 26.57
P_SUTUN_INDEKSI = 16          # 1 tabanlı: A=1 ... P=16

#: İSG ikonlarının yerleştiği alan (V7:W7 birleşik hücresi).
ISG_ILK_SUTUN = 21            # V
ISG_SON_SUTUN = 22            # W
ISG_SATIR = 6                 # satır 7 (0 tabanlı)
ISG_MAKS_YUKSEKLIK = 380000   # EMU — satır 7 yüksekliğine sığar
ISG_ARALIK = 34000            # ikonlar arası boşluk (EMU)

#: CYCLE metin kutusunun blok kenarlarına uzaklığı (şablondaki 1. adımdan ölçüldü).
CYCLE_SAG_BOSLUK = 37160
CYCLE_ALT_BOSLUK = 18900
CYCLE_GENISLIK = 1506434
CYCLE_YUKSEKLIK = 349310


def uret(veri: TalimatVerisi, sablon: str | Path) -> XlsxPackage:
    """Doldurulmuş bir İş Talimatı paketi üretir (henüz diske yazılmaz)."""
    _dogrula(veri)

    pkg = XlsxPackage.open(sablon)
    sheet = SheetPart(pkg.read_text(SHEET_PART))
    _sabitle_p_sutunu(sheet)

    styles = StylePatcher(pkg.read_text("xl/styles.xml"))
    drawing = DrawingPart(pkg.read_text(DRAWING_PART))
    layout = SheetLayout(sheet.xml)

    _yaz_baslik_ve_konu(sheet, styles, veri)
    _yaz_deger_alanlari(sheet, styles, veri)
    _yaz_dokuman_blogu(sheet, veri)
    _yaz_sari_alanlar(sheet, styles, veri)

    _yerlestir_logo(pkg, drawing, veri)
    _yerlestir_isg_ikonlari(pkg, drawing, layout, veri)
    _yerlestir_adimlar(pkg, drawing, layout, veri)

    pkg.write_text(SHEET_PART, sheet.xml)
    pkg.write_text("xl/styles.xml", styles.to_xml())
    pkg.write_text(DRAWING_PART, drawing.to_xml())
    return pkg


# --- Sayfa geometrisi --------------------------------------------------------


def _sabitle_p_sutunu(sheet: SheetPart) -> None:
    """P sütununu sabit genişliğe getirir.

    Şablondaki 27,7109375 değeri baskıda milimetrik kaymaya yol açıyordu.
    Bu, sütun genişliklerine yapılan tek bilinçli müdahaledir.
    """
    sheet.sutun_genisligi_ayarla(P_SUTUN_INDEKSI, P_SUTUN_GENISLIGI)


# --- Hücre yazımı ------------------------------------------------------------


def _yaz_baslik_ve_konu(
    sheet: SheetPart, styles: StylePatcher, veri: TalimatVerisi
) -> None:
    if veri.baslik.strip():
        stil = styles.derive(
            sheet.style_of(BASLIK_HUCRESI), size=PUNTO_BASLIK, bold=True
        )
        metin = veri.baslik.strip()
        if veri.baslik_buyuk_harf:
            # Python'un upper() metodu Türkçe'de 'i' harfini yanlış çevirir.
            metin = textutil.buyut(metin)
        sheet.set_text(BASLIK_HUCRESI, metin, style=stil)

    konu = veri.konu_metni
    if konu:
        # Şablon bu hücreyi ortalı bırakıyordu; talep gereği sola hizalanır.
        stil = styles.derive(
            sheet.style_of(KONU_HUCRESI), size=PUNTO_KONU, horizontal="left"
        )
        sheet.set_text(KONU_HUCRESI, konu, style=stil)


def _yaz_deger_alanlari(
    sheet: SheetPart, styles: StylePatcher, veri: TalimatVerisi
) -> None:
    for alan, hucre in DEGER_HUCRELERI.items():
        # İSG ekipmanı hücresi (V7:W7) ikonlarla kaplanır; ikon seçildiyse
        # metin yazmak çakışmaya yol açar.
        if alan == "isg_ekipmani" and veri.isg_ikonlari:
            continue
        deger = str(getattr(veri, alan) or "").strip()
        if not deger:
            continue
        stil = styles.derive(sheet.style_of(hucre), size=PUNTO_DEGER)
        sheet.set_text(hucre, deger, style=stil)


def _yaz_dokuman_blogu(sheet: SheetPart, veri: TalimatVerisi) -> None:
    """V1:W4 bloğu. Şablonda değerler ': X' biçiminde saklanır."""
    for alan, hucre in DOKUMAN_BLOGU.items():
        deger = str(getattr(veri, alan) or "").strip()
        if deger:
            sheet.set_text(hucre, f": {deger}")


def _yaz_sari_alanlar(
    sheet: SheetPart, styles: StylePatcher, veri: TalimatVerisi
) -> None:
    """Her adımın başlık + açıklamasını sarı hücreye alt alta yazar.

    Başlık KIRMIZI ve kalın, açıklama SİYAH; ikisi de Calibri 14 punto.
    """
    for i, adim in enumerate(veri.adimlar):
        bant, grup = divmod(i, 3)
        satir = 20 + bant * BANT_ADIMI
        hucre = f"{SARI_SUTUNLAR[grup]}{satir}"

        if not adim.dolu:
            if veri.bos_blok_davranisi == "temizle":
                sheet.clear(hucre)
            continue

        runs: list[Run] = []
        if adim.baslik.strip():
            runs.append(
                Run(
                    adim.baslik.strip(),
                    size=PUNTO_SARI,
                    bold=True,
                    color=RENK_BASLIK_KIRMIZI,
                )
            )
        if adim.aciklama.strip():
            if runs:
                runs.append(Run("\n", size=PUNTO_SARI))
            runs.append(
                Run(
                    adim.aciklama.strip(),
                    size=PUNTO_SARI,
                    bold=True,          # kullanıcı talebi: siyah metin de kalın
                    color=RENK_ACIKLAMA_SIYAH,
                )
            )

        stil = styles.derive(sheet.style_of(hucre), size=PUNTO_SARI, wrap=True)
        sheet.set_rich(hucre, runs, style=stil)


# --- Görseller ---------------------------------------------------------------


def _gorsel_ekle(pkg: XlsxPackage, veri: bytes) -> str:
    """Yeni bir görseli pakete ekler ve çizim ilişkisinin rId'sini döndürür."""
    ad = pkg.next_media_name("png")
    pkg.write_bytes(ad, veri)
    pkg.ensure_content_type_default("png", "image/png")
    return pkg.add_relationship(DRAWING_RELS, ad, PIC_REL_TYPE)


def _gorsel_degistir(
    pkg: XlsxPackage, rid: str, gorsel: bytes, cx: int, cy: int
) -> None:
    """Var olan bir ilişkinin işaret ettiği medya parçasının üzerine yazar.

    Yeni medya eklemek yerine mevcut parçayı değiştirmek, şablondaki
    ilişkileri bozmadan yetim (kullanılmayan) görsel kalmasını da önler.
    Görsel, hedef parçanın UZANTISINA UYGUN biçimde kodlanır.
    """
    rels = pkg.read_text(DRAWING_RELS)
    m = re.search(rf'<Relationship[^>]*Id="{rid}"[^>]*Target="([^"]+)"', rels)
    if not m:
        raise SablonHatasi(f"Şablonda {rid} görsel ilişkisi bulunamadı.")
    hedef = m.group(1).replace("../", "xl/").lstrip("/")
    bicim = imaging.bicim_sec(hedef)
    pkg.write_bytes(hedef, imaging.hazirla(gorsel, cx, cy, bicim=bicim))


def _degistir_gorsel_anchor(
    pkg: XlsxPackage,
    drawing: DrawingPart,
    *,
    kaynak_adi: str,
    yeni_ad: str,
    gorsel: bytes,
    cx: int,
    cy: int,
    col: int,
    col_off: int,
    row: int,
    row_off: int,
) -> None:
    """Şablondaki bir görseli, konumunu ve z-sırasını koruyarak değiştirir.

    Anchor `oneCellAnchor` olarak yeniden kurulur: bu anchor tipinde
    `<xdr:ext>` ölçüsü BAĞLAYICIDIR, dolayısıyla istenen tam EMU değeri
    garanti edilir. `twoCellAnchor` kullanılsaydı boyut sütun/satır
    ölçülerinden türetilir ve tam değer tutturulamazdı.
    """
    eski = next((a for a in drawing.find_pictures() if a.name == kaynak_adi), None)
    if eski is None:
        raise SablonHatasi(
            f"Şablonda '{kaynak_adi}' adlı görsel bulunamadı; şablon değişmiş olabilir."
        )

    rid = eski.blip_rid
    if rid is None:
        raise SablonHatasi(f"'{kaynak_adi}' görselinin bağlantısı okunamadı.")

    _gorsel_degistir(pkg, rid, gorsel, cx, cy)

    yer = drawing.index_of(eski)
    drawing.remove(eski)
    drawing.insert(
        yer,
        make_picture_anchor(
            rid=rid,
            shape_id=eski.shape_id,
            name=yeni_ad,
            col=col,
            col_off=col_off,
            row=row,
            row_off=row_off,
            cx=cx,
            cy=cy,
        ),
    )


def _yerlestir_logo(
    pkg: XlsxPackage, drawing: DrawingPart, veri: TalimatVerisi
) -> None:
    """Şablondaki logoyu kullanıcının logosuyla, tam 1,55 x 3,28 cm değiştirir."""
    if not veri.logo:
        return
    _degistir_gorsel_anchor(
        pkg,
        drawing,
        kaynak_adi="Resim 1",
        yeni_ad="Kurum Logosu",
        gorsel=veri.logo,
        cx=LOGO_WIDTH_EMU,
        cy=LOGO_HEIGHT_EMU,
        col=0,
        col_off=83820,
        row=0,
        row_off=76200,
    )


#: Şablondaki İSG piktogramlarının adları (V7:W7 alanında, soldan sağa).
SABLON_ISG_ADLARI = ("Picture 41", "Picture 40", "Picture 39")

#: 1x1 beyaz PNG — kullanılmayan şablon medyasını boşaltmak için.
#: Parça tamamen silinemez, çünkü çıktı doğrulayıcısı şablonun her ZIP
#: parçasının yerinde olmasını şart koşar.
_BOS_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff"
    b"?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _yerlestir_isg_ikonlari(
    pkg: XlsxPackage,
    drawing: DrawingPart,
    layout: SheetLayout,
    veri: TalimatVerisi,
) -> None:
    """V7:W7 alanındaki İSG piktogramlarını seçilen ikonlarla değiştirir.

    Şablondaki hazır piktogramlar küçük ve okunaksızdı. Yerlerine ISO 7010
    biçiminde (mavi daire, beyaz sembol) programatik üretilen ikonlar konur.
    Şablonda 3 piktogram olduğu için ilk 3 ikon mevcut medya parçalarının
    üzerine yazılır; fazlası için yeni parça eklenir.

    NOT: F6:G7'deki SC (özel karakteristik) sembolü sabittir ve hiç
    değiştirilmez — kullanıcıdan istenmez.
    """
    secilenler = [s for s in veri.isg_ikonlari if s in isg_ikonlari.IKONLAR]
    if not secilenler:
        # Hiç ikon seçilmediyse şablona HİÇ dokunulmaz. Sessizce silmek,
        # kullanıcının istemediği bir kayıp olurdu.
        return

    eskiler = [
        a for ad in SABLON_ISG_ADLARI
        if (a := next((p for p in drawing.find_pictures() if p.name == ad), None))
    ]
    if not eskiler:
        return

    ridler = [a.blip_rid for a in eskiler if a.blip_rid]
    yer = min(drawing.index_of(a) for a in eskiler)
    for a in eskiler:
        drawing.remove(a)

    alan_g = layout.cols_emu(ISG_ILK_SUTUN, ISG_SON_SUTUN)
    alan_y = layout.row_emu(ISG_SATIR)
    n = len(secilenler)

    olcu = min(
        ISG_MAKS_YUKSEKLIK,
        alan_y * 9 // 10,
        (alan_g - (n - 1) * ISG_ARALIK) // n,
    )
    toplam = n * olcu + (n - 1) * ISG_ARALIK

    col, col_off = layout.center_offset(ISG_ILK_SUTUN, ISG_SON_SUTUN, toplam)
    row_off = max(0, (alan_y - olcu) // 2)

    # Yerleşimi tek bir yatay eksende hesaplayıp sütuna çeviriyoruz.
    baslangic = sum(layout.col_emu(i) for i in range(ISG_ILK_SUTUN, col)) + col_off

    for sira, ad in enumerate(secilenler):
        png = isg_ikonlari.uret_png(ad, max(64, olcu // 9525 * 4))
        if sira < len(ridler):
            rid = ridler[sira]
            _medya_yaz(pkg, rid, png)
        else:
            rid = _gorsel_ekle_ham(pkg, png)

        x = baslangic + sira * (olcu + ISG_ARALIK)
        i_col, i_off = _coz_ofset(layout.col_emu, ISG_ILK_SUTUN, x)

        drawing.insert(
            yer + sira,
            make_picture_anchor(
                rid=rid,
                shape_id=drawing.next_shape_id(),
                name=f"ISG {ad}",
                col=i_col,
                col_off=i_off,
                row=ISG_SATIR,
                row_off=row_off,
                cx=olcu,
                cy=olcu,
            ),
        )

    # Artan şablon medyası varsa boşalt.
    for rid in ridler[n:]:
        _medya_yaz(pkg, rid, _BOS_PNG)


def _medya_yaz(pkg: XlsxPackage, rid: str, veri: bytes) -> None:
    """Bir ilişkinin işaret ettiği medya parçasının üzerine ham bayt yazar."""
    rels = pkg.read_text(DRAWING_RELS)
    m = re.search(rf'<Relationship[^>]*Id="{rid}"[^>]*Target="([^"]+)"', rels)
    if not m:
        raise SablonHatasi(f"Şablonda {rid} görsel ilişkisi bulunamadı.")
    pkg.write_bytes(m.group(1).replace("../", "xl/").lstrip("/"), veri)


def _gorsel_ekle_ham(pkg: XlsxPackage, veri: bytes) -> str:
    ad = pkg.next_media_name("png")
    pkg.write_bytes(ad, veri)
    pkg.ensure_content_type_default("png", "image/png")
    return pkg.add_relationship(DRAWING_RELS, ad, PIC_REL_TYPE)


#: Şablondaki tek CYCLE metin kutusunun metni (1. adıma ait).
SABLON_CYCLE_METNI = "CYCLE: 3 SN"


def temizlenecek_kutular(veri: TalimatVerisi) -> list[str]:
    """Kullanıcının isteğiyle SİLİNECEK metin kutularının şablondaki metinleri.

    Hem üretici hem çıktı doğrulayıcısı bu tek kaynağı kullanır; böylece
    "kullanıcı sildi" ile "program kaybetti" ayrımı ikisinde de aynı kalır.
    """
    if veri.bos_blok_davranisi != "temizle":
        return []

    silinecek = [
        f"{i + 1}. KONTROL ADIMI"
        for i, adim in enumerate(veri.adimlar)
        if not adim.dolu
    ]
    ilk = veri.adimlar[0]
    if not ilk.dolu or ilk.cycle_sn is None:
        silinecek.append(SABLON_CYCLE_METNI)
    return silinecek


def _yerlestir_adimlar(
    pkg: XlsxPackage,
    drawing: DrawingPart,
    layout: SheetLayout,
    veri: TalimatVerisi,
) -> None:
    """Adım görsellerini, başlık ve CYCLE metin kutularını yerleştirir."""
    cycle_kaynak = drawing.find_by_text(SABLON_CYCLE_METNI)
    if cycle_kaynak is None:
        raise GirdiHatasi(
            "Şablondaki CYCLE metin kutusu bulunamadı; şablon değişmiş olabilir."
        )

    baslik_kutulari = {
        n: drawing.find_by_text(f"{n}. KONTROL ADIMI") for n in range(1, 10)
    }
    silinecek = set(temizlenecek_kutular(veri))

    if SABLON_CYCLE_METNI in silinecek:
        drawing.remove(cycle_kaynak)
        cycle_kaynak_kullanilabilir = False
    else:
        cycle_kaynak_kullanilabilir = True

    for i, adim in enumerate(veri.adimlar):
        bant, grup = divmod(i, 3)
        ilk_sutun, son_sutun = SUTUN_GRUPLARI[grup]
        ilk_satir = BANT_ILK_SATIR + bant * BANT_ADIMI
        son_satir = BANT_SON_SATIR + bant * BANT_ADIMI

        kutu = baslik_kutulari.get(i + 1)

        if not adim.dolu:
            # (b) seçeneği: bloğun başlık ve cycle metin kutularını temizle.
            if kutu is not None and f"{i + 1}. KONTROL ADIMI" in silinecek:
                drawing.remove(kutu)
            continue

        # 1) Görsel — tam 5 x 17 cm, yatay ortalı, üstten hizalı.
        if adim.gorsel:
            islenmis = imaging.hazirla(
                adim.gorsel, STEP_IMAGE_WIDTH_EMU, STEP_IMAGE_HEIGHT_EMU
            )
            rid = _gorsel_ekle(pkg, islenmis)
            col, col_off = layout.center_offset(
                ilk_sutun, son_sutun, STEP_IMAGE_WIDTH_EMU
            )
            anchor = make_picture_anchor(
                rid=rid,
                shape_id=drawing.next_shape_id(),
                name=f"Kontrol Adimi {i + 1} Gorseli",
                col=col,
                col_off=col_off,
                row=ilk_satir,
                row_off=0,
                cx=STEP_IMAGE_WIDTH_EMU,
                cy=STEP_IMAGE_HEIGHT_EMU,
            )
            # Z-SIRASI: ilk <xdr:sp>'den önce eklenir, yani TÜM metin
            # kutularının arkasında kalır. "Send to back" gereksinimi budur.
            drawing.insert_before_shapes(anchor)

        # 2) Başlık metin kutusu — şablondaki yerinde kalır, metni sabittir.
        if kutu is not None:
            kutu.set_text(f"{i + 1}. KONTROL ADIMI")

        # 3) CYCLE metin kutusu.
        if adim.cycle_sn is not None:
            metin = f"CYCLE: {adim.cycle_sn} SN"
            if i == 0 and cycle_kaynak_kullanilabilir:
                cycle_kaynak.set_text(metin)
            else:
                x = (
                    layout.cols_emu(ilk_sutun, son_sutun)
                    - CYCLE_GENISLIK
                    - CYCLE_SAG_BOSLUK
                )
                y = (
                    layout.rows_emu(ilk_satir, son_satir)
                    - CYCLE_YUKSEKLIK
                    - CYCLE_ALT_BOSLUK
                )
                col, col_off = _coz_ofset(layout.col_emu, ilk_sutun, max(0, x))
                row, row_off = _coz_ofset(layout.row_emu, ilk_satir, max(0, y))
                drawing.append(
                    clone_textbox(
                        cycle_kaynak,
                        shape_id=drawing.next_shape_id(),
                        name=f"Cycle {i + 1}",
                        metin=metin,
                        col=col,
                        col_off=col_off,
                        row=row,
                        row_off=row_off,
                        genislik=CYCLE_GENISLIK,
                        yukseklik=CYCLE_YUKSEKLIK,
                        sutun_genisligi=layout.col_emu,
                        satir_yuksekligi=layout.row_emu,
                    )
                )


def silinen_isg_gorseli(veri: TalimatVerisi) -> int:
    """İSG alanında şablondan ÇIKARILAN piktogram sayısı.

    Şablonda 3 piktogram vardır. Kullanıcı 3'ten az ikon seçerse aradaki
    fark bilinçli olarak silinir; çıktı doğrulayıcısı bunu "kayıp" saymamalı.
    """
    secilenler = [s for s in veri.isg_ikonlari if s in isg_ikonlari.IKONLAR]
    if not secilenler:
        return 0        # hiç seçim yoksa şablona dokunulmaz
    return max(0, len(SABLON_ISG_ADLARI) - len(secilenler))


def bos_sablon(sablon: str | Path) -> XlsxPackage:
    """Hiç veri girilmemiş, şablonun birebir kopyası olan paketi döndürür (1.10).

    Şablon dosyasının kendisi asla taşınmaz/değiştirilmez; her zaman kopya
    üzerinde çalışılır.
    """
    return XlsxPackage.open(sablon)


def _coz_ofset(olcu, baslangic: int, mesafe: int) -> tuple[int, int]:
    """`baslangic` indeksinden `mesafe` EMU ötedeki (indeks, ofset) çiftini bulur."""
    i = baslangic
    kalan = mesafe
    while True:
        w = olcu(i)
        if kalan < w or w <= 0:
            return i, int(kalan)
        kalan -= w
        i += 1


# --- Girdi doğrulaması -------------------------------------------------------

#: Sarı alanın taşmadan alabileceği yaklaşık karakter sayısı (14 punto).
SARI_ALAN_KARAKTER_SINIRI = 250


def _dogrula(veri: TalimatVerisi) -> None:
    if not veri.baslik.strip():
        raise GirdiHatasi("Talimat adı boş bırakılamaz.")
    if len(veri.adimlar) != 9:
        raise GirdiHatasi(
            f"Kontrol adımı sayısı 9 olmalı, {len(veri.adimlar)} adım verildi."
        )
    if veri.bos_blok_davranisi not in ("cerceveli", "temizle"):
        raise GirdiHatasi(
            "Boş blok davranışı yalnızca 'cerceveli' veya 'temizle' olabilir."
        )

    for i, adim in enumerate(veri.adimlar, start=1):
        if adim.cycle_sn is not None and adim.cycle_sn < 0:
            raise GirdiHatasi(f"{i}. adımın cycle süresi negatif olamaz.")
        uzunluk = len(adim.baslik.strip()) + len(adim.aciklama.strip())
        if uzunluk > SARI_ALAN_KARAKTER_SINIRI:
            raise GirdiHatasi(
                f"{i}. adımın başlık ve açıklaması sarı alana sığmıyor "
                f"({uzunluk} karakter, sınır {SARI_ALAN_KARAKTER_SINIRI}). "
                "Metni kısaltın — program metni sessizce kırpmaz."
            )
