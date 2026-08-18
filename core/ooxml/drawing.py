"""xl/drawings/drawing1.xml üzerinde çizim nesnesi cerrahisi.

Çizim nesneleri (metin kutuları, görseller) XML metni olarak ham biçimde
tutulur ve yalnızca hedeflenen bölümler değiştirilir. Böylece şablondaki
biçim, kenarlık, tema referansları ve creationId'ler aynen korunur.

Z-SIRASI KURALI
    drawing1.xml içindeki anchor sırası doğrudan z-sırasıdır: listede daha
    ÖNCE gelen nesne daha ARKADA kalır. Kontrol adımı görselleri bu yüzden
    metin kutularından önceki konumlara yerleştirilir.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from ..errors import SablonHatasi

# Bir anchor'ın kapsayabileceği üst düzey etiketler.
_ANCHOR_TAGS = ("twoCellAnchor", "oneCellAnchor", "absoluteAnchor")

_PIC_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
)


@dataclass
class Anchor:
    """drawing1.xml içindeki tek bir üst düzey çizim nesnesi."""

    kind: str          # twoCellAnchor | oneCellAnchor | absoluteAnchor
    xml: str           # açılış ve kapanış etiketleri dahil ham XML

    # --- Okuma ---------------------------------------------------------------

    # Bazı araçlar (örn. openpyxl) çizim XML'ini `xdr:` öneki yerine varsayılan
    # ad alanıyla yazar. Okuma tarafı her iki biçimi de tanımalıdır; aksi halde
    # doğrulayıcı böyle bir dosyayı ayrıştıramaz ve denetim yapamaz.

    @property
    def shape_kind(self) -> str:
        """sp (metin kutusu/şekil), pic (görsel), graphicFrame vb."""
        m = re.search(r"<(?:xdr:)?(sp|pic|graphicFrame|cxnSp|grpSp)[\s>]", self.xml)
        return m.group(1) if m else "?"

    @property
    def name(self) -> str:
        m = re.search(r'<(?:xdr:)?cNvPr[^>]*\sname="([^"]*)"', self.xml)
        return html.unescape(m.group(1)) if m else ""

    @property
    def shape_id(self) -> int:
        m = re.search(r'<(?:xdr:)?cNvPr\s+id="(\d+)"', self.xml)
        return int(m.group(1)) if m else 0

    @property
    def text(self) -> str:
        """Şeklin tüm metin çalışmalarının birleşimi."""
        return "".join(
            html.unescape(t) for t in re.findall(r"<a:t>(.*?)</a:t>", self.xml, re.S)
        )

    @property
    def from_marker(self) -> tuple[int, int, int, int]:
        """(sütun, sütun ofseti, satır, satır ofseti) — 0 tabanlı."""
        m = re.search(r"<(?:xdr:)?from>(.*?)</(?:xdr:)?from>", self.xml, re.S)
        if not m:
            return (0, 0, 0, 0)
        i = m.group(1)

        def al(etiket: str) -> int:
            g = re.search(rf"<(?:xdr:)?{etiket}>(-?\d+)</(?:xdr:)?{etiket}>", i)
            return int(g.group(1)) if g else 0

        return al("col"), al("colOff"), al("row"), al("rowOff")

    @property
    def offset(self) -> tuple[int, int]:
        """xfrm içindeki mutlak (x, y) konumu — nesneleri konuma göre eşleştirmek için."""
        m = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/>', self.xml)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    @property
    def blip_rid(self) -> str | None:
        """Görselin gömülü olduğu ilişki kimliği (rId...)."""
        m = re.search(r'<a:blip[^>]*\sr:embed="([^"]+)"', self.xml)
        return m.group(1) if m else None

    @property
    def ext(self) -> tuple[int, int] | None:
        """oneCellAnchor için bağlayıcı ölçü, twoCellAnchor için xfrm önbelleği."""
        m = re.search(r'<xdr:ext cx="(\d+)" cy="(\d+)"/>', self.xml) or re.search(
            r'<a:ext cx="(\d+)" cy="(\d+)"/>', self.xml
        )
        return (int(m.group(1)), int(m.group(2))) if m else None

    @property
    def fill_color(self) -> str | None:
        """Şeklin DOLGU rengi (6 haneli RGB); yoksa None.

        DİKKAT: `<xdr:spPr>` içinde dolgudan sonra bir de `<a:ln>` (kenarlık)
        gelir ve onun da kendi `<a:solidFill>` bloğu vardır. Tüm spPr içinde
        arama yapmak kenarlık rengini dolgu sanmaya yol açar. Bu yüzden
        yalnızca `<a:ln>` ÖNCESİNDEKİ bölge taranır.

        Tema rengiyle (`schemeClr`) doldurulmuş şekiller de None döner:
        çağıran taraf için anlamlı olan "belirli bir RGB dolgusu var mı"
        sorusudur.
        """
        bolge = _dolgu_bolgesi(self.xml)
        if bolge is None or "<a:noFill/>" in bolge:
            return None
        c = re.search(r'<a:solidFill>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', bolge)
        return c.group(1).upper() if c else None

    # --- Yazma ---------------------------------------------------------------

    def set_text(self, yeni_metin: str) -> None:
        """Metin kutusunun yazısını değiştirir, biçimini korur.

        İlk `<a:r>` çalışmasının `<a:rPr>` biçimi alınır; paragrafın diğer tüm
        çalışmaları silinip tek çalışma bırakılır. Böylece punto, kalınlık,
        renk ve hizalama şablondaki gibi kalır.
        """
        body = re.search(r"<xdr:txBody>.*?</xdr:txBody>", self.xml, re.S)
        if not body:
            raise SablonHatasi(
                f'"{self.name}" adlı çizim nesnesinde metin alanı bulunamadı.'
            )
        old_body = body.group(0)

        rpr = re.search(r"<a:r><a:rPr[^>]*?(?:/>|>.*?</a:rPr>)", old_body, re.S)
        rpr_xml = rpr.group(0)[len("<a:r>"):] if rpr else '<a:rPr lang="tr-TR"/>'

        run = f"<a:r>{rpr_xml}<a:t>{_esc(yeni_metin)}</a:t></a:r>"

        # Paragrafın pPr'sini koru, içindeki tüm çalışmaları tek çalışmayla değiştir.
        def _repl_para(m: re.Match) -> str:
            para = m.group(0)
            ppr = re.search(r"<a:pPr[^>]*?(?:/>|>.*?</a:pPr>)", para, re.S)
            return f"<a:p>{ppr.group(0) if ppr else ''}{run}</a:p>"

        new_body = re.sub(r"<a:p>.*?</a:p>", _repl_para, old_body, count=1, flags=re.S)
        # İlk paragraftan sonraki paragrafları at.
        paras = re.findall(r"<a:p>.*?</a:p>", new_body, re.S)
        if len(paras) > 1:
            for extra in paras[1:]:
                new_body = new_body.replace(extra, "", 1)

        self.xml = self.xml.replace(old_body, new_body, 1)

    def clear_text(self) -> None:
        """Metni siler ama kutuyu (çerçevesiyle birlikte) yerinde bırakır."""
        self.set_text("")

    def set_fill(self, renk: str | None) -> None:
        """Şeklin DOLGUSUNU değiştirir. `renk=None` ise `<a:noFill/>` uygulanır.

        Yalnızca `<a:ln>` ÖNCESİNDEKİ dolgu bölgesine dokunulur; KENARLIK
        (renk, kalınlık, tema referansı) aynen korunur. DrawingML şema sırası
        gereği dolgu, geometriden sonra ve kenarlıktan önce yer alır.

        Bu ayrım kritiktir: kenarlığın da kendi `<a:solidFill>` bloğu vardır
        ve tüm spPr üzerinde arama yapmak, dolgu yerine çerçeveyi boyamaya
        yol açar.

        TNE onay kutuları bu yolla işaretlenir: işaretli = 00B050 (yeşil).
        """
        m = re.search(r"<xdr:spPr>(.*?)</xdr:spPr>", self.xml, re.S)
        if not m:
            raise SablonHatasi(f'"{self.name}" nesnesinin biçim alanı bulunamadı.')

        bas, kuyruk = _spPr_parcala(m.group(1))

        # Mevcut dolgu tanımı ne olursa olsun kaldırılır: noFill, solidFill,
        # gradFill, blipFill, pattFill, grpFill.
        bas = _DOLGU_DESENI.sub("", bas)

        yeni = (
            "<a:noFill/>"
            if renk is None
            else f'<a:solidFill><a:srgbClr val="{renk.upper()}"/></a:solidFill>'
        )
        self.xml = self.xml.replace(
            m.group(0), f"<xdr:spPr>{bas}{yeni}{kuyruk}</xdr:spPr>", 1
        )

    def set_identity(self, shape_id: int, name: str) -> None:
        """cNvPr id/name değerlerini değiştirir ve creationId'yi tekilleştirir."""
        self.xml = re.sub(
            r'(<xdr:cNvPr\s+)id="\d+"\s+name="[^"]*"',
            rf'\1id="{shape_id}" name="{_esc(name)}"',
            self.xml,
            count=1,
        )
        # Klonlanan şekillerin creationId'si benzersiz olmalı.
        self.xml = re.sub(
            r'(<a16:creationId[^>]*\sid=")\{[^}]*\}(")',
            rf"\g<1>{{{_uid(shape_id)}}}\g<2>",
            self.xml,
            count=1,
        )

    def move(self, dx: int, dy: int, sutun_genislikleri, satir_yukseklikleri) -> None:
        """Anchor'ı EMU cinsinden kaydırır (from ve to işaretçilerinin ikisi de)."""
        for tag in ("from", "to"):
            m = re.search(rf"<xdr:{tag}>(.*?)</xdr:{tag}>", self.xml, re.S)
            if not m:
                continue
            inner = m.group(1)
            col = int(re.search(r"<xdr:col>(\d+)</xdr:col>", inner).group(1))
            coff = int(re.search(r"<xdr:colOff>(-?\d+)</xdr:colOff>", inner).group(1))
            row = int(re.search(r"<xdr:row>(\d+)</xdr:row>", inner).group(1))
            roff = int(re.search(r"<xdr:rowOff>(-?\d+)</xdr:rowOff>", inner).group(1))

            col, coff = _shift(col, coff, dx, sutun_genislikleri)
            row, roff = _shift(row, roff, dy, satir_yukseklikleri)

            self.xml = self.xml.replace(
                m.group(0),
                f"<xdr:{tag}><xdr:col>{col}</xdr:col><xdr:colOff>{coff}</xdr:colOff>"
                f"<xdr:row>{row}</xdr:row><xdr:rowOff>{roff}</xdr:rowOff></xdr:{tag}>",
                1,
            )

    def clone(self) -> "Anchor":
        return Anchor(self.kind, self.xml)


def _shift(index: int, offset: int, delta: int, olcu) -> tuple[int, int]:
    """Bir (hücre indeksi, ofset) çiftini EMU cinsinden kaydırıp normalize eder."""
    pos = sum(olcu(i) for i in range(index)) + offset + delta
    pos = max(0, pos)
    i = 0
    while True:
        w = olcu(i)
        if pos < w or w <= 0:
            break
        pos -= w
        i += 1
    return i, int(pos)


class DrawingPart:
    """drawing1.xml'in düzenlenebilir modeli: sıralı anchor listesi."""

    def __init__(self, xml: str):
        self._prolog, self._anchors, self._epilog = _split_anchors(xml)

    # --- Liste erişimi -------------------------------------------------------

    @property
    def anchors(self) -> list[Anchor]:
        return self._anchors

    def __len__(self) -> int:
        return len(self._anchors)

    def find_by_text(self, metin: str) -> Anchor | None:
        for a in self._anchors:
            if a.text.strip() == metin.strip():
                return a
        return None

    def find_all_shapes(self) -> list[Anchor]:
        return [a for a in self._anchors if a.shape_kind == "sp"]

    def find_pictures(self) -> list[Anchor]:
        return [a for a in self._anchors if a.shape_kind == "pic"]

    def index_of(self, anchor: Anchor) -> int:
        for i, a in enumerate(self._anchors):
            if a is anchor:
                return i
        raise ValueError("Anchor bu çizim parçasına ait değil.")

    def next_shape_id(self) -> int:
        return max((a.shape_id for a in self._anchors), default=1) + 1

    # --- Değiştirme ----------------------------------------------------------

    def insert(self, index: int, anchor: Anchor) -> None:
        self._anchors.insert(index, anchor)

    def append(self, anchor: Anchor) -> None:
        self._anchors.append(anchor)

    def remove(self, anchor: Anchor) -> None:
        self._anchors.remove(anchor)

    def send_to_back(self, anchor: Anchor) -> None:
        """Nesneyi listenin başına alır: tüm diğer nesnelerin arkasında kalır."""
        self._anchors.remove(anchor)
        self._anchors.insert(0, anchor)

    def insert_before_shapes(self, anchor: Anchor) -> None:
        """Nesneyi ilk `<xdr:sp>` şeklinden hemen önce yerleştirir.

        Görselin tüm metin kutularının ARKASINDA kalmasını garanti eder,
        ancak varsa logo/piktogram gibi diğer görsellerin sırasını bozmaz.
        """
        for i, a in enumerate(self._anchors):
            if a.shape_kind == "sp":
                self._anchors.insert(i, anchor)
                return
        self._anchors.append(anchor)

    def to_xml(self) -> str:
        return self._prolog + "".join(a.xml for a in self._anchors) + self._epilog


# --- Anchor üreticileri ------------------------------------------------------


def make_picture_anchor(
    *,
    rid: str,
    shape_id: int,
    name: str,
    col: int,
    col_off: int,
    row: int,
    row_off: int,
    cx: int,
    cy: int,
) -> Anchor:
    """Tam ölçülü bir görsel için `oneCellAnchor` üretir.

    `oneCellAnchor` seçilmesinin sebebi: bu anchor tipinde `<xdr:ext>` ölçüsü
    BAĞLAYICIDIR. `twoCellAnchor` kullanılsaydı görselin boyutu sütun
    genişliklerinden türetilir ve istenen tam EMU değeri garanti edilemezdi.
    """
    return Anchor(
        "oneCellAnchor",
        "<xdr:oneCellAnchor>"
        f"<xdr:from><xdr:col>{col}</xdr:col><xdr:colOff>{col_off}</xdr:colOff>"
        f"<xdr:row>{row}</xdr:row><xdr:rowOff>{row_off}</xdr:rowOff></xdr:from>"
        f'<xdr:ext cx="{cx}" cy="{cy}"/>'
        '<xdr:pic><xdr:nvPicPr>'
        f'<xdr:cNvPr id="{shape_id}" name="{_esc(name)}">'
        '<a:extLst><a:ext uri="{FF2B5EF4-FFF2-40B4-BE49-F238E27FC236}">'
        '<a16:creationId xmlns:a16="http://schemas.microsoft.com/office/drawing/2014/main" '
        f'id="{{{_uid(shape_id)}}}"/></a:ext></a:extLst></xdr:cNvPr>'
        "<xdr:cNvPicPr><a:picLocks noChangeAspect=\"1\"/></xdr:cNvPicPr></xdr:nvPicPr>"
        "<xdr:blipFill>"
        f'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rid}"/>'
        "<a:stretch><a:fillRect/></a:stretch></xdr:blipFill>"
        "<xdr:spPr>"
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        "</xdr:spPr></xdr:pic><xdr:clientData/></xdr:oneCellAnchor>",
    )


def clone_textbox(
    kaynak: Anchor,
    *,
    shape_id: int,
    name: str,
    metin: str,
    col: int,
    col_off: int,
    row: int,
    row_off: int,
    genislik: int,
    yukseklik: int,
    sutun_genisligi,
    satir_yuksekligi,
) -> Anchor:
    """Var olan bir metin kutusunu biçimiyle birlikte klonlayıp konumlandırır.

    Şablonda yalnızca 1 adet CYCLE metin kutusu bulunduğu için kalan 8 adım
    bu fonksiyonla üretilir; kenarlık, dolgu, punto ve hizalama kaynaktan
    birebir devralınır.
    """
    yeni = kaynak.clone()
    yeni.set_identity(shape_id, name)
    yeni.set_text(metin)

    bitis_col, bitis_coff = _shift(col, col_off, genislik, sutun_genisligi)
    bitis_row, bitis_roff = _shift(row, row_off, yukseklik, satir_yuksekligi)

    for tag, (c, co, r, ro) in (
        ("from", (col, col_off, row, row_off)),
        ("to", (bitis_col, bitis_coff, bitis_row, bitis_roff)),
    ):
        yeni.xml = re.sub(
            rf"<xdr:{tag}>.*?</xdr:{tag}>",
            f"<xdr:{tag}><xdr:col>{c}</xdr:col><xdr:colOff>{co}</xdr:colOff>"
            f"<xdr:row>{r}</xdr:row><xdr:rowOff>{ro}</xdr:rowOff></xdr:{tag}>",
            yeni.xml,
            count=1,
            flags=re.S,
        )

    # twoCellAnchor'da <a:xfrm> yalnızca önbellektir (Excel açılışta from/to
    # işaretçilerinden yeniden hesaplar), ancak bazı görüntüleyiciler bu değeri
    # olduğu gibi kullanır. Bayat kalmaması için birlikte güncelleniyor.
    mutlak_x = sum(sutun_genisligi(i) for i in range(col)) + col_off
    mutlak_y = sum(satir_yuksekligi(i) for i in range(row)) + row_off
    yeni.xml = re.sub(
        r'<a:off x="-?\d+" y="-?\d+"/>',
        f'<a:off x="{mutlak_x}" y="{mutlak_y}"/>',
        yeni.xml,
        count=1,
    )
    yeni.xml = re.sub(
        r'<a:ext cx="\d+" cy="\d+"/>',
        f'<a:ext cx="{genislik}" cy="{yukseklik}"/>',
        yeni.xml,
        count=1,
    )
    return yeni


# --- Yardımcılar -------------------------------------------------------------


def _split_anchors(xml: str) -> tuple[str, list[Anchor], str]:
    """Çizim XML'ini (önek, anchor listesi, sonek) olarak parçalar.

    Hem `<xdr:twoCellAnchor>` hem de öneksiz `<twoCellAnchor>` biçimini tanır.
    Hiç anchor bulunamazsa boş liste döner — bu bir hata değil, doğrulayıcının
    "tüm çizim nesneleri silinmiş" bulgusunu üretebilmesi için gereken durumdur.
    """
    pattern = re.compile(
        r"<(xdr:)?(" + "|".join(_ANCHOR_TAGS) + r")\b[^>]*>.*?</\1?\2>", re.S
    )
    anchors: list[Anchor] = []
    prolog = None
    son = 0
    for m in pattern.finditer(xml):
        if prolog is None:
            prolog = xml[: m.start()]
        anchors.append(Anchor(m.group(2), m.group(0)))
        son = m.end()

    if prolog is None:
        # Çizim katmanı var ama içi boş: gövdeyi önek/sonek olarak ayır.
        kok = re.search(r"<(?:xdr:)?wsDr\b[^>]*>", xml)
        if kok:
            return xml[: kok.end()], [], xml[kok.end():]
        raise SablonHatasi("Çizim katmanı okunamadı; dosya beklenen yapıda değil.")
    return prolog, anchors, xml[son:]


#: spPr icindeki TUM dolgu tanimlari. Geri referans (backreference)
#: kullanilmaz; her tip acikca yazilir, boylece desen okunur ve guvenlidir.
_DOLGU_DESENI = re.compile(
    r"<a:noFill\s*/>"
    r"|<a:grpFill\s*/>"
    r"|<a:solidFill\b[^>]*/>"
    r"|<a:solidFill\b[^>]*>.*?</a:solidFill>"
    r"|<a:gradFill\b[^>]*/>"
    r"|<a:gradFill\b[^>]*>.*?</a:gradFill>"
    r"|<a:blipFill\b[^>]*/>"
    r"|<a:blipFill\b[^>]*>.*?</a:blipFill>"
    r"|<a:pattFill\b[^>]*/>"
    r"|<a:pattFill\b[^>]*>.*?</a:pattFill>"
    ,
    re.S,
)


def _spPr_parcala(ic: str) -> tuple[str, str]:
    """spPr icerigini (dolgunun yazilacagi bas, dokunulmayacak kuyruk) olarak ayirir.

    Kuyruk `<a:ln>` ile baslar; kenarlik ve efektler oradadir ve dolgu
    islemleri bu bolgeye ASLA dokunmamalidir.
    """
    for etiket in ("<a:ln>", "<a:ln ", "<a:effectLst", "<a:scene3d", "<a:sp3d"):
        i = ic.find(etiket)
        if i != -1:
            return ic[:i], ic[i:]
    return ic, ""


def _dolgu_bolgesi(xml: str) -> str | None:
    """Bir seklin spPr dolgu bolgesini dondurur (kenarlik haric)."""
    m = re.search(r"<xdr:spPr>(.*?)</xdr:spPr>", xml, re.S)
    return _spPr_parcala(m.group(1))[0] if m else None


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _uid(n: int) -> str:
    """Şekil id'sinden türetilen, çakışmayan bir GUID benzeri değer."""
    return f"00000000-0008-0000-0000-{n:012X}"


PIC_REL_TYPE = _PIC_REL_TYPE
