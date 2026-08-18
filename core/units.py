"""Ölçü birimi dönüşümleri ve proje sabitleri.

Tüm ölçüler OOXML'in doğal birimi olan EMU (English Metric Unit) cinsinden
tutulur. Yaklaşık değer kullanılmaz; sabitler tam sayı olarak tanımlanmıştır.
"""

from __future__ import annotations

# --- Temel dönüşümler --------------------------------------------------------

EMU_PER_CM = 360000
EMU_PER_INCH = 914400
EMU_PER_PIXEL = 9525          # 96 DPI: 914400 / 96
EMU_PER_POINT = 12700         # 72 pt = 1 inch
PIXELS_PER_CM = 37.7952755905512   # 96 / 2.54

# Excel'in "maximum digit width" değeri: Calibri 11pt için 7 piksel.
MAX_DIGIT_WIDTH = 7

# Şablonlarda tanımlı olmayan satırların varsayılan yüksekliği (punto).
DEFAULT_ROW_HEIGHT_PT = 15.0


def cm_to_emu(cm: float) -> int:
    return int(round(cm * EMU_PER_CM))


def emu_to_cm(emu: int) -> float:
    return emu / EMU_PER_CM


def px_to_emu(px: float) -> int:
    return int(round(px * EMU_PER_PIXEL))


def emu_to_px(emu: int) -> float:
    return emu / EMU_PER_PIXEL


def pt_to_emu(pt: float) -> int:
    return int(round(pt * EMU_PER_POINT))


def col_width_to_px(width: float) -> int:
    """Excel sütun genişliğini (karakter birimi) piksele çevirir.

    Excel'in belgelenmiş formülü. Genişlik değeri dolgu payını zaten içerir.
    """
    return int((256 * width + int(128 / MAX_DIGIT_WIDTH)) / 256 * MAX_DIGIT_WIDTH)


def col_width_to_emu(width: float) -> int:
    return col_width_to_px(width) * EMU_PER_PIXEL


def row_height_to_emu(height_pt: float | None) -> int:
    if height_pt is None:
        height_pt = DEFAULT_ROW_HEIGHT_PT
    return pt_to_emu(height_pt)


# --- Görev tanımında verilen zorunlu ölçüler ---------------------------------
# Bu değerler talimatta açıkça belirtilmiştir ve "yaklaşık" uygulanmaz.

#: Kurum logosu: 1,55 cm yükseklik x 3,28 cm genişlik
LOGO_HEIGHT_EMU = 558000       # 1,55 cm
LOGO_WIDTH_EMU = 1180800       # 3,28 cm

#: Kontrol adımı görseli: 5 cm yükseklik x 17 cm genişlik
STEP_IMAGE_HEIGHT_EMU = 1800000    # 5 cm
STEP_IMAGE_WIDTH_EMU = 6120000     # 17 cm

#: TNE eğitim/parça görseli: 41,75 cm genişlik x 23,72 cm yükseklik.
#: Sayfa %59 ölçekle basıldığı için kağıttaki karşılığı ~24,6 x 14,0 cm'dir.
TNE_IMAGE_WIDTH_EMU = 15030000     # 41,75 cm
TNE_IMAGE_HEIGHT_EMU = 8539200     # 23,72 cm

# Doğrulama: sabitlerin dönüşüm formülleriyle tutarlı olduğunu garanti et.
assert LOGO_HEIGHT_EMU == cm_to_emu(1.55)
assert LOGO_WIDTH_EMU == cm_to_emu(3.28)
assert STEP_IMAGE_HEIGHT_EMU == cm_to_emu(5)
assert STEP_IMAGE_WIDTH_EMU == cm_to_emu(17)
assert TNE_IMAGE_WIDTH_EMU == cm_to_emu(41.75)
assert TNE_IMAGE_HEIGHT_EMU == cm_to_emu(23.72)
