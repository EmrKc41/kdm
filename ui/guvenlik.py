"""Oturum doğrulaması.

Bu katman ARAYÜZ katmanına aittir, belge motoruna değil: `core/` şablon
doldurmaktan sorumludur ve kimlik kavramını hiç bilmez.

Neden çerez, neden başlık değil? İSG ikonları arayüzde `<img src="/api/...">`
ile yükleniyor; tarayıcı `<img>` isteklerine Authorization başlığı EKLEMEZ.
Çerez ise kendiliğinden gider, dolayısıyla tek bir mekanizma hem fetch hem
görsel isteklerini kapsar. Çerez HttpOnly'dir; sayfadaki JavaScript okuyamaz.
"""

from __future__ import annotations

import hmac
import os
import secrets
import time

#: Çerez adı — arayüz bu adı bilmek zorunda değildir (HttpOnly).
CEREZ = "kdu_oturum"

#: Oturum ömrü. Bir vardiya boyunca yeniden giriş istememek için 12 saat.
OMUR_SN = 12 * 60 * 60


def _ayar(ad: str, varsayilan: str) -> str:
    return os.environ.get(ad, varsayilan)


def kullanici_adi() -> str:
    return _ayar("KDU_KULLANICI", "admin")


def parola() -> str:
    return _ayar("KDU_PAROLA", "admin")


#: Bellekte tutulan jetonlar: {jeton: son_gecerlilik}.
#: Tek süreçli bir masaüstü uygulaması için yeterlidir. Sunucu yeniden
#: başlarsa (geliştirmede `--reload`) oturumlar düşer ve yeniden giriş
#: istenir; bu bilinçli bir kabuldür, kalıcı depo eklenmemiştir.
_jetonlar: dict[str, float] = {}


def _ayikla() -> None:
    simdi = time.time()
    for j in [j for j, bitis in _jetonlar.items() if bitis <= simdi]:
        _jetonlar.pop(j, None)


def dogrula(gelen_kullanici: str, gelen_parola: str) -> bool:
    """Kimlik bilgilerini sabit süreli karşılaştırmayla denetler.

    `compare_digest` kullanılır: normal `==` karşılaştırması ilk farklı
    karakterde durur ve yanıt süresinden parola hakkında bilgi sızdırır.

    Kullanıcı adı ASCII olduğu için DEĞİŞMEZ küçültme kullanılır. Türkçe
    kuralı burada yanlış olurdu: "ADMIN" → "admın" (noktasız ı).
    """
    ad_dogru = hmac.compare_digest(
        gelen_kullanici.strip().lower(), kullanici_adi().lower()
    )
    parola_dogru = hmac.compare_digest(gelen_parola, parola())
    # İki denetim de her durumda çalışır; erken çıkış zamanlama farkı yaratır.
    return ad_dogru and parola_dogru


def jeton_uret() -> str:
    _ayikla()
    jeton = secrets.token_urlsafe(32)
    _jetonlar[jeton] = time.time() + OMUR_SN
    return jeton


def gecerli_mi(jeton: str | None) -> bool:
    if not jeton:
        return False
    _ayikla()
    return jeton in _jetonlar


def sonlandir(jeton: str | None) -> None:
    if jeton:
        _jetonlar.pop(jeton, None)


def hepsini_sil() -> None:
    """Testler için: jeton deposunu boşaltır."""
    _jetonlar.clear()
