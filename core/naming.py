"""Dosya adı üretimi.

Format: "<KONU>_<DOKUMAN_TIPI>_<TARIH>.xlsx"

Türkçe karakterler içerikte UTF-8 olarak korunur, ancak DOSYA ADINDA güvenli
ASCII karşılıklarına dönüştürülür; böylece dosya farklı işletim sistemleri ve
ağ paylaşımları arasında sorunsuz taşınır.
"""

from __future__ import annotations

import re
from datetime import date

TURKCE_ESLEME = str.maketrans(
    {
        "ç": "c", "Ç": "C",
        "ğ": "g", "Ğ": "G",
        "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O",
        "ş": "s", "Ş": "S",
        "ü": "u", "Ü": "U",
    }
)

DOKUMAN_TIPLERI = {
    "talimat": "IS_TALIMATI",
    "tne": "TEK_NOKTA_EGITIMI",
    "vardiya": "VARDIYA_LISTESI",
    "rapor": "KALITE_RAPORU",
}

MAKS_KONU_UZUNLUGU = 60


def guvenli(metin: str) -> str:
    """Bir metni dosya adında kullanılabilir hale getirir."""
    metin = metin.translate(TURKCE_ESLEME)
    metin = re.sub(r"[^\w\s-]", "", metin, flags=re.ASCII)
    metin = re.sub(r"[\s_-]+", "_", metin).strip("_")
    return metin.upper()


def dosya_adi(konu: str, tip: str, tarih: date | str | None = None) -> str:
    """'<KONU>_<DOKUMAN_TIPI>_<TARIH>.xlsx' biçiminde dosya adı üretir."""
    parca = guvenli(konu)[:MAKS_KONU_UZUNLUGU]
    dokuman = DOKUMAN_TIPLERI.get(tip, guvenli(tip))

    if tarih is None:
        tarih = date.today()
    if isinstance(tarih, date):
        tarih_metni = tarih.strftime("%d.%m.%Y")
    else:
        # Tarihteki noktalar dosya adında korunur; yalnızca güvensiz
        # karakterler ayıklanır.
        tarih_metni = re.sub(r"[^\d.]", "", str(tarih)).strip(".")
        tarih_metni = tarih_metni or date.today().strftime("%d.%m.%Y")

    # Konu verilmemişse "ADSIZ" gibi bir doldurma eklenmez; doküman tipi
    # zaten dosyayı tanımlar. (TNE arayüzü konu sormaz.)
    onek = f"{parca}_" if parca else ""
    return f"{onek}{dokuman}_{tarih_metni}.xlsx"
