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

    Karşılaştırma BAYT üzerinden yapılır. `compare_digest` metin verilirse
    ASCII dışı karakterde `TypeError` fırlatır; Türkçe bir kullanıcı adı
    ya da parola ("müdür", "şifre") temiz bir 401 yerine 500 üretirdi ve
    KDU_PAROLA'ya Türkçe parola konamazdı.

    Kullanıcı adında DEĞİŞMEZ küçültme kullanılır. Türkçe kuralı burada
    yanlış olurdu: "ADMIN" → "admın" (noktasız ı).
    """
    ad_dogru = hmac.compare_digest(
        gelen_kullanici.strip().lower().encode("utf-8"),
        kullanici_adi().lower().encode("utf-8"),
    )
    parola_dogru = hmac.compare_digest(
        gelen_parola.encode("utf-8"), parola().encode("utf-8")
    )
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
    """Testler için: jeton deposunu ve deneme sayacını boşaltır."""
    _jetonlar.clear()
    _basarisiz.clear()


# --- Kaba kuvvet yavaşlatması ------------------------------------------------
#
# Ölçüm: sınır yokken 30 yanlış parola 0,2 saniyede denenebiliyordu (~150
# deneme/sn). admin/admin ile bunun önemi yok, ama KDU_PAROLA ile gerçek bir
# parola konduğunda tek bir gece boyunca milyonlarca deneme yapılabilirdi.
#
# Sayaç KÜRESELDİR, istemci adresine göre değil: istekler Next.js
# yönlendiricisi üzerinden geldiği için motora hepsi 127.0.0.1'den ulaşır ve
# adrese göre ayırmak yanıltıcı bir güven verirdi. Bunun bedeli, saldırganın
# gerçek kullanıcıyı da kısa süre kilitleyebilmesidir; bu yüzden kilit
# BİLEREK kısa tutulur (30 sn) ve başarılı girişte sayaç sıfırlanır.

#: Kilit devreye girmeden önceki ardışık başarısız deneme sayısı.
SINIR = 8

#: Kilit süresi (saniye).
KILIT_SN = 30

#: Her başarısız denemeye eklenen gecikme. Betikle saniyede yüzlerce deneme
#: yapmayı anlamsız kılar, elle yanlış yazan kullanıcıyı ise rahatsız etmez.
GECIKME_SN = 0.3

_basarisiz: dict[str, float | int] = {}


def kilitli_kalan_sn() -> int:
    """Kilit açıksa kalan saniye, değilse 0."""
    bitis = float(_basarisiz.get("kilit_bitis", 0))
    kalan = bitis - time.time()
    return int(kalan) + 1 if kalan > 0 else 0


def basarisiz_kaydet() -> None:
    sayi = int(_basarisiz.get("sayi", 0)) + 1
    _basarisiz["sayi"] = sayi
    if sayi >= SINIR:
        _basarisiz["kilit_bitis"] = time.time() + KILIT_SN
        _basarisiz["sayi"] = 0


def basarili_kaydet() -> None:
    _basarisiz.clear()
