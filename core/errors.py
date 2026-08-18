"""Uygulamaya özgü hata tipleri.

Kullanıcıya asla stack trace gösterilmez; bu sınıfların `mesaj` alanı doğrudan
arayüzde gösterilebilecek, anlaşılır Türkçe metin içerir.
"""

from __future__ import annotations


class UygulamaHatasi(Exception):
    """Kullanıcıya gösterilebilir tüm hataların ortak atası."""

    def __init__(self, mesaj: str, detay: str | None = None):
        super().__init__(mesaj)
        self.mesaj = mesaj
        self.detay = detay


class SablonHatasi(UygulamaHatasi):
    """Şablon dosyası okunamadı veya beklenen yapıda değil."""


class GirdiHatasi(UygulamaHatasi):
    """Kullanıcı girdisi doğrulamayı geçemedi."""


class GorselHatasi(UygulamaHatasi):
    """Yüklenen görsel işlenemedi."""


class DogrulamaHatasi(UygulamaHatasi):
    """Üretilen dosya çıktı doğrulamasını geçemedi.

    Bu hata fırlatıldığında dosya diske YAZILMAZ. Program hiçbir koşulda
    sessizce bozuk dosya üretmez.
    """

    def __init__(self, mesaj: str, bulgular: list[str] | None = None):
        super().__init__(mesaj, detay="\n".join(bulgular or []))
        self.bulgular = bulgular or []
