"""xl/worksheets/sheetN.xml üzerinde hücre değeri yazma.

Değerler `inlineStr` olarak yazılır. Böylece sharedStrings.xml'e hiç
dokunulmaz ve mevcut paylaşılan metinlerin indeksleri kaymaz. `inlineStr`
zengin metni de destekler: sarı açıklama alanındaki "kırmızı kalın başlık +
siyah açıklama" tek hücrede iki ayrı çalışma (run) olarak üretilir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import SablonHatasi


@dataclass
class Run:
    """Bir hücre içindeki tek biçimli metin parçası."""

    text: str
    size: float | None = None
    bold: bool = False
    color: str | None = None          # "FF0000" gibi 6 haneli RGB
    font: str = "Calibri"

    def to_xml(self) -> str:
        props = ""
        if self.bold:
            props += "<b/>"
        if self.size is not None:
            props += f'<sz val="{self.size:g}"/>'
        if self.color:
            props += f'<color rgb="FF{self.color.upper().lstrip("#")}"/>'
        props += f'<rFont val="{self.font}"/><family val="2"/><charset val="162"/>'
        return f"<r><rPr>{props}</rPr><t xml:space=\"preserve\">{esc(self.text)}</t></r>"


def paylasilan_metinler(shared_strings_xml: str) -> list[str]:
    """sharedStrings.xml'i sıralı metin listesine çevirir.

    Bir `<si>` birden çok `<r>` çalışması içerebilir; hepsi birleştirilir.
    """
    metinler: list[str] = []
    for si in re.findall(r"<si>(.*?)</si>", shared_strings_xml, re.S):
        parcalar = re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)
        metinler.append(unesc("".join(parcalar)))
    return metinler


class SheetPart:
    """Bir çalışma sayfası XML'inin düzenlenebilir modeli."""

    def __init__(self, xml: str, paylasilan: list[str] | None = None):
        self._xml = xml
        self._paylasilan = paylasilan or []

    @property
    def xml(self) -> str:
        return self._xml

    # --- Okuma ---------------------------------------------------------------

    def text_of(self, ref: str) -> str:
        """Hücrenin görünen metnini döndürür (paylaşılan veya satır içi)."""
        m = self._find(ref)
        if not m:
            return ""
        hucre = m.group(0)

        if 't="s"' in hucre:
            v = re.search(r"<v>(\d+)</v>", hucre)
            if v and int(v.group(1)) < len(self._paylasilan):
                return self._paylasilan[int(v.group(1))]
            return ""
        if 't="inlineStr"' in hucre:
            return unesc("".join(re.findall(r"<t[^>]*>(.*?)</t>", hucre, re.S)))
        v = re.search(r"<v>(.*?)</v>", hucre, re.S)
        return unesc(v.group(1)) if v else ""

    def etiketi_koruyarak_yaz(
        self, ref: str, deger: str, *, style: int | None = None
    ) -> None:
        """Etiket ve değeri aynı hücrede tutan alanlar için.

        TNE şablonunda "MÜDÜRLÜK / BİRİM :", "KISIM :", "SAYFA NO   : 1/1"
        gibi alanlarda etiket ve değer TEK hücrede saklanır. Bu metot
        etiketi (son iki nokta dahil) aynen korur ve yalnızca sonrasını yazar.
        """
        mevcut = self.text_of(ref)
        if ":" in mevcut:
            onek = mevcut[: mevcut.rindex(":") + 1]
        else:
            onek = mevcut.rstrip()
        self.set_text(ref, f"{onek} {deger}".rstrip(), style=style)

    def style_of(self, ref: str) -> int:
        """Hücrenin mevcut stil indeksini döndürür."""
        m = self._find(ref)
        if not m:
            raise SablonHatasi(f"Şablonda {ref} hücresi bulunamadı.")
        s = re.search(r'\ss="(\d+)"', m.group(0))
        return int(s.group(1)) if s else 0

    def exists(self, ref: str) -> bool:
        return self._find(ref) is not None

    # --- Yazma ---------------------------------------------------------------

    def set_text(self, ref: str, deger: str, *, style: int | None = None) -> None:
        """Hücreye düz metin yazar. Boş metin hücreyi değersiz bırakır."""
        self._write(ref, f"<is><t xml:space=\"preserve\">{esc(deger)}</t></is>"
                    if deger else None, style)

    def set_rich(self, ref: str, runs: list[Run], *, style: int | None = None) -> None:
        """Hücreye çok biçimli (zengin) metin yazar."""
        dolu = [r for r in runs if r.text]
        icerik = "<is>" + "".join(r.to_xml() for r in dolu) + "</is>" if dolu else None
        self._write(ref, icerik, style)

    def clear(self, ref: str) -> None:
        """Hücrenin değerini siler, biçimini korur."""
        self._write(ref, None, None)

    def sutun_genisligi_ayarla(self, index: int, genislik: float) -> None:
        """Tek bir sütunun genişliğini değiştirir (1 tabanlı indeks).

        Yalnızca hedef `<col>` tanımının `width` niteliği değişir; diğer
        nitelikler, sıraları ve komşu tanımlar aynen korunur. Hedef sütun
        başka sütunlarla ortak bir aralıkta tanımlanmışsa aralık önce
        bölünür, böylece komşular etkilenmez.
        """
        def _degistir(m: re.Match) -> str:
            etiket, alt, ust = m.group(0), int(m.group(1)), int(m.group(2))
            if not (alt <= index <= ust):
                return etiket

            def _w(parca: str, deger: float) -> str:
                return re.sub(r'width="[\d.]+"', f'width="{deger:g}"', parca, count=1)

            def _aralik(parca: str, a: int, u: int) -> str:
                parca = re.sub(r'min="\d+"', f'min="{a}"', parca, count=1)
                return re.sub(r'max="\d+"', f'max="{u}"', parca, count=1)

            parcalar = []
            if alt < index:
                parcalar.append(_aralik(etiket, alt, index - 1))
            parcalar.append(_w(_aralik(etiket, index, index), genislik))
            if ust > index:
                parcalar.append(_aralik(etiket, index + 1, ust))
            return "".join(parcalar)

        self._xml = re.sub(
            r'<col min="(\d+)" max="(\d+)"[^>]*/>', _degistir, self._xml
        )

    def set_style(self, ref: str, style: int) -> None:
        m = self._find(ref)
        if not m:
            raise SablonHatasi(f"Şablonda {ref} hücresi bulunamadı.")
        eski = m.group(0)
        yeni = re.sub(r'\ss="\d+"', f' s="{style}"', eski) if ' s="' in eski \
            else eski.replace(f'<c r="{ref}"', f'<c r="{ref}" s="{style}"', 1)
        self._xml = self._xml.replace(eski, yeni, 1)

    # --- İç ------------------------------------------------------------------

    def _find(self, ref: str) -> re.Match | None:
        # Kendi kendine kapanan biçim AYRI bir dal olmalı. Tek dalda
        # "(?:/>|>.*?</c>)" yazılırsa geri izleme sırasında ikinci seçenek
        # devreye girer ve eşleşme komşu hücreleri de yutar.
        return re.search(
            rf'<c r="{ref}"[^>]*/>|<c r="{ref}"[^>]*>.*?</c>', self._xml, re.S
        )

    def _write(self, ref: str, icerik: str | None, style: int | None) -> None:
        m = self._find(ref)
        if not m:
            raise SablonHatasi(
                f"Şablonda {ref} hücresi bulunamadı; hücre haritası değişmiş olabilir."
            )
        eski = m.group(0)

        s = re.search(r'\ss="(\d+)"', eski)
        stil = style if style is not None else (int(s.group(1)) if s else None)
        stil_attr = f' s="{stil}"' if stil is not None else ""

        yeni = (
            f'<c r="{ref}"{stil_attr}/>'
            if icerik is None
            else f'<c r="{ref}"{stil_attr} t="inlineStr">{icerik}</c>'
        )
        self._xml = self._xml.replace(eski, yeni, 1)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def unesc(s: str) -> str:
    return (
        s.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&amp;", "&")
    )
