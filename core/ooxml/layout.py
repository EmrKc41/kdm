"""Sayfa geometrisi: sütun genişlikleri ve satır yükseklikleri.

Çizim nesnelerini doğru hücrelere çapalamak için sayfanın gerçek ölçülerine
ihtiyaç var. Bu değerler sheet XML'indeki <cols> ve <row> tanımlarından
okunur; tanımlanmamış olanlar için varsayılanlar kullanılır.
"""

from __future__ import annotations

import re

from ..units import (
    DEFAULT_ROW_HEIGHT_PT,
    col_width_to_emu,
    row_height_to_emu,
)


class SheetLayout:
    def __init__(self, sheet_xml: str):
        self._col_widths: dict[int, float] = {}
        self._default_col = 8.43

        fmt = re.search(r'<sheetFormatPr\b[^>]*defaultColWidth="([\d.]+)"', sheet_xml)
        if fmt:
            self._default_col = float(fmt.group(1))

        cols = re.search(r"<cols>(.*?)</cols>", sheet_xml, re.S)
        if cols:
            for m in re.finditer(
                r'<col\s+min="(\d+)"\s+max="(\d+)"\s+width="([\d.]+)"', cols.group(1)
            ):
                lo, hi, w = int(m.group(1)), int(m.group(2)), float(m.group(3))
                for c in range(lo, min(hi, 16384) + 1):
                    self._col_widths[c - 1] = w

        self._row_heights: dict[int, float] = {}
        for m in re.finditer(r'<row\s+r="(\d+)"[^>]*\sht="([\d.]+)"', sheet_xml):
            self._row_heights[int(m.group(1)) - 1] = float(m.group(2))

        dr = re.search(r'<sheetFormatPr\b[^>]*defaultRowHeight="([\d.]+)"', sheet_xml)
        self._default_row = float(dr.group(1)) if dr else DEFAULT_ROW_HEIGHT_PT

    # --- Tekil ölçüler (0 tabanlı indeks) ------------------------------------

    def col_emu(self, index: int) -> int:
        return col_width_to_emu(self._col_widths.get(index, self._default_col))

    def row_emu(self, index: int) -> int:
        return row_height_to_emu(self._row_heights.get(index, self._default_row))

    # --- Aralık ölçüleri -----------------------------------------------------

    def cols_emu(self, start: int, end: int) -> int:
        """[start, end] aralığındaki sütunların toplam genişliği (dahil)."""
        return sum(self.col_emu(i) for i in range(start, end + 1))

    def rows_emu(self, start: int, end: int) -> int:
        """[start, end] aralığındaki satırların toplam yüksekliği (dahil)."""
        return sum(self.row_emu(i) for i in range(start, end + 1))

    def center_offset(self, start_col: int, end_col: int, genislik: int) -> tuple[int, int]:
        """Bir sütun grubunda `genislik` kadar nesneyi yatayda ortalar.

        (başlangıç sütunu, sütun içi ofset) döndürür. Nesne gruptan genişse
        gruba sol kenardan yaslanır.
        """
        toplam = self.cols_emu(start_col, end_col)
        bosluk = max(0, toplam - genislik)
        kayma = bosluk // 2

        col = start_col
        while kayma >= self.col_emu(col) and col < end_col:
            kayma -= self.col_emu(col)
            col += 1
        return col, int(kayma)
