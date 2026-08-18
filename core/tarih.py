"""Türkçe tarih yardımcıları.

Vardiya listesinin sayfa adı, tarihin ayın kaçıncı haftasına düştüğünden
türetilir: 17 Ağustos -> "Ağustos3.Hafta".
"""

from __future__ import annotations

import re
from datetime import date

AYLAR = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


def coz(deger: str | date | None) -> date | None:
    """'GG.AA.YYYY' veya 'YYYY-AA-GG' biçimindeki metni tarihe çevirir."""
    if isinstance(deger, date):
        return deger
    if not deger:
        return None

    metin = str(deger).strip()
    m = re.fullmatch(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", metin)
    if m:
        gun, ay, yil = (int(x) for x in m.groups())
    else:
        m = re.fullmatch(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", metin)
        if not m:
            return None
        yil, ay, gun = (int(x) for x in m.groups())

    try:
        return date(yil, ay, gun)
    except ValueError:
        return None


def ayin_haftasi(tarih: date) -> int:
    """Tarihin ayın kaçıncı haftasına düştüğünü döndürür (1-5).

    Ayın ilk 7 günü 1. hafta, sonraki 7 günü 2. hafta biçiminde sayılır.
    17 Ağustos -> 3. hafta.
    """
    return (tarih.day - 1) // 7 + 1


def hafta_adi(deger: str | date | None) -> str:
    """Excel sayfa adı için 'Ağustos3.Hafta' biçiminde metin üretir.

    Tarih çözülemezse bugünün tarihi kullanılır.
    """
    tarih = coz(deger) or date.today()
    return f"{AYLAR[tarih.month - 1]}{ayin_haftasi(tarih)}.Hafta"
