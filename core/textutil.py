"""Türkçe'ye duyarlı metin işlemleri.

Python'un yerleşik `str.upper()` / `str.lower()` metotları Türkçe'de HATALIDIR:

    'Talimatı'.upper()  ->  'TALIMATI'   (yanlış: i -> I)
    doğrusu             ->  'TALİMATI'   (i -> İ, ı -> I)

Fabrika dokümanlarında başlıklar büyük harfle yazıldığı için bu fark doğrudan
çıktıya yansır; o yüzden dönüşüm burada elle yapılır.
"""

from __future__ import annotations

_BUYUK = str.maketrans({"i": "İ", "ı": "I"})
_KUCUK = str.maketrans({"I": "ı", "İ": "i"})


def buyut(metin: str) -> str:
    """Türkçe kurallarına göre büyük harfe çevirir."""
    return metin.translate(_BUYUK).upper()


def kucult(metin: str) -> str:
    """Türkçe kurallarına göre küçük harfe çevirir."""
    return metin.translate(_KUCUK).lower()


def kirpma_yok(metin: str, sinir: int) -> bool:
    """Metnin sınıra sığıp sığmadığını bildirir. Kırpma YAPMAZ."""
    return len(metin) <= sinir
