"""xl/styles.xml üzerinde punto/kalınlık/renk türetme.

Şablonun mevcut stilleri ASLA değiştirilmez. Bir hücrenin puntosu
değiştirilmek istendiğinde mevcut `xf` kaydı klonlanır, klonun font'u
türetilir ve yeni kayıtlar listelerin SONUNA eklenir. Böylece aynı stili
paylaşan diğer hücreler etkilenmez.
"""

from __future__ import annotations

import re

from ..errors import SablonHatasi


class StylePatcher:
    def __init__(self, xml: str):
        self._xml = xml
        self._fonts = _extract(xml, "fonts", "font")
        self._cellxfs = _extract(xml, "cellXfs", "xf")
        self._cache: dict[tuple, int] = {}

    # --- Sorgu ---------------------------------------------------------------

    def font_of(self, xf_index: int) -> str:
        """Bir stil kaydının kullandığı font XML'ini döndürür."""
        return self._fonts[self._font_id(xf_index)]

    def font_size_of(self, xf_index: int) -> float | None:
        m = re.search(r'<sz val="([\d.]+)"', self.font_of(xf_index))
        return float(m.group(1)) if m else None

    def _font_id(self, xf_index: int) -> int:
        if xf_index >= len(self._cellxfs):
            raise SablonHatasi(f"Şablonda {xf_index} numaralı stil kaydı yok.")
        m = re.search(r'fontId="(\d+)"', self._cellxfs[xf_index])
        return int(m.group(1)) if m else 0

    # --- Türetme -------------------------------------------------------------

    def derive(
        self,
        xf_index: int,
        *,
        size: float | None = None,
        bold: bool | None = None,
        color: str | None = None,
        wrap: bool | None = None,
        horizontal: str | None = None,
    ) -> int:
        """Verilen stilden türetilmiş yeni bir stil indeksi döndürür.

        Hiçbir değişiklik istenmemişse orijinal indeks aynen döner.
        Aynı türetme daha önce yapıldıysa önbellekten dönülür.
        """
        if (
            size is None
            and bold is None
            and color is None
            and wrap is None
            and horizontal is None
        ):
            return xf_index

        key = (xf_index, size, bold, color, wrap, horizontal)
        if key in self._cache:
            return self._cache[key]

        font_xml = self._fonts[self._font_id(xf_index)]
        yeni_font = _patch_font(font_xml, size=size, bold=bold, color=color)

        if yeni_font == font_xml:
            yeni_font_id = self._font_id(xf_index)
        elif yeni_font in self._fonts:
            yeni_font_id = self._fonts.index(yeni_font)
        else:
            self._fonts.append(yeni_font)
            yeni_font_id = len(self._fonts) - 1

        yeni_xf = _patch_xf(
            self._cellxfs[xf_index], yeni_font_id, wrap, horizontal
        )
        if yeni_xf in self._cellxfs:
            yeni_index = self._cellxfs.index(yeni_xf)
        else:
            self._cellxfs.append(yeni_xf)
            yeni_index = len(self._cellxfs) - 1

        self._cache[key] = yeni_index
        return yeni_index

    # --- Yazma ---------------------------------------------------------------

    def to_xml(self) -> str:
        xml = _replace(self._xml, "fonts", self._fonts)
        xml = _replace(xml, "cellXfs", self._cellxfs)
        return xml


# --- Yardımcılar -------------------------------------------------------------


def _extract(xml: str, container: str, child: str) -> list[str]:
    m = re.search(rf"<{container}\b[^>]*>(.*?)</{container}>", xml, re.S)
    if not m:
        raise SablonHatasi(f"Şablonun stil tanımında <{container}> bölümü yok.")
    return re.findall(rf"<{child}\b[^>]*?(?:/>|>.*?</{child}>)", m.group(1), re.S)


def _replace(xml: str, container: str, items: list[str]) -> str:
    yeni = f'<{container} count="{len(items)}">' + "".join(items) + f"</{container}>"
    return re.sub(rf"<{container}\b[^>]*>.*?</{container}>", lambda _: yeni, xml,
                  count=1, flags=re.S)


def _patch_font(
    font_xml: str, *, size: float | None, bold: bool | None, color: str | None
) -> str:
    inner = re.sub(r"^<font\b[^>]*>|</font>$|^<font\b[^>]*/>$", "", font_xml).strip()
    if font_xml.endswith("/>") and not inner:
        inner = ""

    if size is not None:
        deger = f"{size:g}"
        inner = (
            re.sub(r'<sz val="[\d.]+"\s*/>', f'<sz val="{deger}"/>', inner)
            if "<sz " in inner
            else inner + f'<sz val="{deger}"/>'
        )
    if bold is not None:
        inner = re.sub(r"<b\s*/>", "", inner)
        if bold:
            inner = "<b/>" + inner
    if color is not None:
        renk = f'<color rgb="FF{color.upper().lstrip("#")}"/>'
        inner = (
            re.sub(r"<color\b[^>]*/>", renk, inner, count=1)
            if "<color" in inner
            else inner + renk
        )
    return f"<font>{inner}</font>"


def _nitelik_ayarla(xf: str, ad: str, deger: str) -> str:
    """`<xf>` etiketine bir niteliği ekler veya günceller (tekrar etmeden)."""
    if re.search(rf'\s{ad}="', xf):
        return re.sub(rf'\s{ad}="[^"]*"', f' {ad}="{deger}"', xf, count=1)
    return xf.replace("<xf ", f'<xf {ad}="{deger}" ', 1)


def _patch_xf(
    xf_xml: str, font_id: int, wrap: bool | None, horizontal: str | None
) -> str:
    xf = re.sub(r'fontId="\d+"', f'fontId="{font_id}"', xf_xml)
    if 'fontId="' not in xf:
        xf = xf.replace("<xf ", f'<xf fontId="{font_id}" ', 1)
    xf = _nitelik_ayarla(xf, "applyFont", "1")

    if wrap is None and horizontal is None:
        return xf

    # Mevcut hizalama niteliklerini koru, yalnızca istenenleri değiştir.
    m = re.search(r"<alignment\b([^>]*?)/>", xf)
    nitelikler: dict[str, str] = (
        dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))) if m else {}
    )
    if wrap is not None:
        nitelikler["wrapText"] = "1" if wrap else "0"
    if horizontal is not None:
        nitelikler["horizontal"] = horizontal

    yeni = (
        "<alignment "
        + " ".join(f'{k}="{v}"' for k, v in nitelikler.items())
        + "/>"
    )

    if m:
        xf = xf.replace(m.group(0), yeni, 1)
    elif xf.endswith("/>"):
        xf = xf[:-2] + ">" + yeni + "</xf>"
    else:
        xf = xf.replace("</xf>", yeni + "</xf>")

    return _nitelik_ayarla(xf, "applyAlignment", "1")
