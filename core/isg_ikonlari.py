"""İSG (iş sağlığı ve güvenliği) ekipman ikonlarının üretimi.

Şablondaki hazır piktogramlar küçük ve okunaksızdı. Bunlar yerine ISO 7010
"zorunluluk" işaretleri biçiminde — mavi daire üzerine beyaz sembol —
operatörün bir bakışta anlayabileceği ikonlar programatik olarak çizilir.

İkonlar vektörel bir kaynağa değil, doğrudan Pillow ilkellerine dayanır;
böylece hiçbir harici dosya veya font bağımlılığı oluşmaz ve ikonlar her
çözünürlükte keskin üretilebilir.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

from .errors import GirdiHatasi

#: ISO 7010 zorunluluk işaretlerinin mavisi.
MAVI = (0, 87, 166)
BEYAZ = (255, 255, 255)

#: İkonların çizildiği referans tuval. Çıktı bu boyuttan ölçeklenir.
TUVAL = 256

#: Arayüzde gösterilecek sıra ve etiketler.
IKONLAR: dict[str, str] = {
    "baret": "Baret",
    "gozluk": "Koruyucu Gözlük",
    "kulaklik": "Kulaklık",
    "eldiven": "Eldiven",
    "ayakkabi": "Emniyet Ayakkabısı",
    "maske": "Toz Maskesi",
    "yelek": "Reflektif Yelek",
    "siperlik": "Yüz Siperliği",
}


def uret(ad: str, boyut: int = TUVAL) -> Image.Image:
    """Tek bir İSG ikonunu RGB görüntü olarak üretir."""
    if ad not in IKONLAR:
        raise GirdiHatasi(
            f"'{ad}' tanınmayan bir İSG ekipmanı. "
            "Seçenekler: " + ", ".join(IKONLAR)
        )

    img = Image.new("RGB", (TUVAL, TUVAL), BEYAZ)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, TUVAL - 5, TUVAL - 5), fill=MAVI)

    _CIZICILER[ad](d)

    if boyut != TUVAL:
        img = img.resize((boyut, boyut), Image.LANCZOS)
    return img


def uret_png(ad: str, boyut: int = TUVAL) -> bytes:
    tampon = io.BytesIO()
    uret(ad, boyut).save(tampon, format="PNG", optimize=True)
    return tampon.getvalue()


def serit(adlar: list[str], ikon_px: int, aralik_px: int) -> list[bytes]:
    """Seçilen ikonları aynı ölçüde PNG listesi olarak üretir."""
    return [uret_png(ad, ikon_px) for ad in adlar]


# --- Tekil piktogramlar ------------------------------------------------------
# Koordinatlar 256x256 tuvale göredir. Semboller beyaz, ayrıntı çizgileri
# maviyle "oyularak" verilir; böylece küçük ölçekte de siluet okunur kalır.


def _baret(d: ImageDraw.ImageDraw) -> None:
    # Yüz
    d.ellipse((84, 132, 172, 214), fill=BEYAZ)
    # Kask kubbesi
    d.pieslice((52, 58, 204, 186), 180, 360, fill=BEYAZ)
    # Siperlik
    d.rounded_rectangle((36, 116, 220, 140), radius=12, fill=BEYAZ)
    # Kubbe ile yüzü ayıran boşluk
    d.rectangle((36, 140, 220, 146), fill=MAVI)
    # Kask sırtı
    d.rectangle((122, 64, 134, 116), fill=MAVI)


def _gozluk(d: ImageDraw.ImageDraw) -> None:
    # Baş silueti — tek elips, küçük ölçekte parçalanmasın
    d.ellipse((74, 52, 182, 200), fill=BEYAZ)
    # Gözlüğün oturduğu mavi şerit
    d.rounded_rectangle((38, 94, 218, 140), radius=22, fill=MAVI)
    # Camlar
    d.rounded_rectangle((50, 102, 116, 132), radius=14, fill=BEYAZ)
    d.rounded_rectangle((140, 102, 206, 132), radius=14, fill=BEYAZ)
    # Burun köprüsü
    d.rectangle((116, 110, 140, 122), fill=BEYAZ)


def _kulaklik(d: ImageDraw.ImageDraw) -> None:
    # Baş
    d.ellipse((78, 74, 178, 174), fill=BEYAZ)
    d.rounded_rectangle((88, 150, 168, 214), radius=22, fill=BEYAZ)
    # Kafa bandı
    d.arc((48, 44, 208, 204), 180, 360, fill=BEYAZ, width=20)
    # Kulaklıklar
    d.rounded_rectangle((32, 108, 82, 182), radius=18, fill=BEYAZ)
    d.rounded_rectangle((174, 108, 224, 182), radius=18, fill=BEYAZ)
    # Bandı baştan ayır
    d.arc((60, 56, 196, 192), 180, 360, fill=MAVI, width=8)


def _eldiven(d: ImageDraw.ImageDraw) -> None:
    # Parmaklar
    for x in (86, 112, 138, 164):
        d.rounded_rectangle((x, 44, x + 22, 132), radius=11, fill=BEYAZ)
    # Baş parmak
    d.rounded_rectangle((44, 118, 86, 190), radius=21, fill=BEYAZ)
    # Avuç
    d.rounded_rectangle((80, 104, 192, 214), radius=24, fill=BEYAZ)
    # Bilek bandı
    d.rectangle((80, 196, 192, 206), fill=MAVI)
    # Parmak araları
    for x in (108, 134, 160):
        d.rectangle((x, 48, x + 6, 108), fill=MAVI)


def _ayakkabi(d: ImageDraw.ImageDraw) -> None:
    # Bot silueti (profilden, burun sağda)
    d.polygon(
        [
            (48, 196), (48, 92), (92, 92), (100, 132),
            (140, 142), (186, 158), (212, 176), (212, 196),
        ],
        fill=BEYAZ,
    )
    # Taban ayrımı
    d.rectangle((48, 178, 212, 186), fill=MAVI)
    # Bilek katı
    d.rectangle((48, 118, 96, 126), fill=MAVI)
    # Çelik burun vurgusu
    d.arc((150, 140, 220, 190), 200, 340, fill=MAVI, width=7)


def _maske(d: ImageDraw.ImageDraw) -> None:
    # Bağcıklar — maskenin iki yanından yatay çıkar
    d.line((26, 112, 76, 118), fill=BEYAZ, width=12)
    d.line((230, 112, 180, 118), fill=BEYAZ, width=12)
    # Maske gövdesi
    d.rounded_rectangle((58, 88, 198, 190), radius=40, fill=BEYAZ)
    # Kıvrımlar — tek çizgi yerine iki ince oyuk, siluet bölünmez
    d.rectangle((72, 126, 184, 134), fill=MAVI)
    d.rectangle((72, 154, 184, 162), fill=MAVI)


def _yelek(d: ImageDraw.ImageDraw) -> None:
    # Gövde — tek parça siluet. Küçük ölçekte okunurluğu korumak için
    # oyuk sayısı bilinçli olarak azaltıldı (yaka + tek reflektif bant).
    d.polygon(
        [
            (76, 62), (180, 62), (196, 92),
            (196, 206), (60, 206), (60, 92),
        ],
        fill=BEYAZ,
    )
    # Kol oyukları — sığ tutuldu, aksi halde siluet taç gibi görünüyor
    d.ellipse((40, 50, 76, 118), fill=MAVI)
    d.ellipse((180, 50, 216, 118), fill=MAVI)
    # Yaka — sığ çentik
    d.polygon([(112, 62), (128, 92), (144, 62)], fill=MAVI)
    # Reflektif bant
    d.rectangle((60, 148, 196, 164), fill=MAVI)


def _siperlik(d: ImageDraw.ImageDraw) -> None:
    # Baş üstü
    d.pieslice((84, 46, 172, 166), 180, 360, fill=BEYAZ)
    # Alın bandı
    d.rounded_rectangle((46, 68, 210, 100), radius=15, fill=BEYAZ)
    # Bant ile siperliği ayıran boşluk
    d.rectangle((46, 100, 210, 112), fill=MAVI)
    # Siperlik camı — alın bandının altından aşağı kavisli tek parça
    d.pieslice((44, 2, 212, 224), 0, 180, fill=BEYAZ)
    # Cam üzerindeki yansıma çizgisi
    d.arc((72, 60, 184, 208), 20, 160, fill=MAVI, width=8)


_CIZICILER = {
    "baret": _baret,
    "gozluk": _gozluk,
    "kulaklik": _kulaklik,
    "eldiven": _eldiven,
    "ayakkabi": _ayakkabi,
    "maske": _maske,
    "yelek": _yelek,
    "siperlik": _siperlik,
}
