"""Kötüye kullanıma karşı korumaların testleri.

Buradaki her testin arkasında ÖLÇÜLMÜŞ bir açık vardır; sayılar tahmin
değil, düzeltme öncesi gözlenen davranıştan gelir.
"""

from __future__ import annotations

import io
import zipfile

import pytest

pytest.importorskip("fastapi")

from core import importers                     # noqa: E402
from core.errors import GirdiHatasi            # noqa: E402
from tests.asgi_istemci import AsgiIstemci     # noqa: E402
from ui import guvenlik                        # noqa: E402
from ui.app import app                         # noqa: E402


@pytest.fixture
def temiz():
    guvenlik.hepsini_sil()
    yield AsgiIstemci(app)
    guvenlik.hepsini_sil()


# --- Kaba kuvvet -------------------------------------------------------------


def test_ardisik_hatali_denemeler_kilitlenir(temiz):
    """Düzeltme öncesi 30 yanlış parola 0,2 saniyede denenebiliyordu."""
    for _ in range(guvenlik.SINIR):
        yanit = temiz.post(
            "/api/oturum/giris", json={"kullanici": "admin", "parola": "yanlis"}
        )
        assert yanit.status_code == 401

    kilitli = temiz.post(
        "/api/oturum/giris", json={"kullanici": "admin", "parola": "yanlis"}
    )
    assert kilitli.status_code == 429
    assert "Retry-After" in kilitli.headers or "retry-after" in kilitli.headers


def test_kilitliyken_dogru_parola_da_kabul_edilmez(temiz):
    for _ in range(guvenlik.SINIR):
        temiz.post("/api/oturum/giris", json={"kullanici": "admin", "parola": "x"})
    assert temiz.giris().status_code == 429


def test_basarili_giris_sayaci_sifirlar(temiz):
    for _ in range(guvenlik.SINIR - 1):
        temiz.post("/api/oturum/giris", json={"kullanici": "admin", "parola": "x"})

    assert temiz.giris().status_code == 200
    # Sayaç sıfırlandığı için yeniden tam sınır kadar hakkımız olmalı.
    for _ in range(guvenlik.SINIR - 1):
        assert temiz.post(
            "/api/oturum/giris", json={"kullanici": "admin", "parola": "x"}
        ).status_code == 401


# --- Gövde boyutu ------------------------------------------------------------


def test_devasa_govde_okunmadan_reddedilir(temiz):
    """Düzeltme öncesi kimlik istemeyen giriş ucu 100 MB'lık gövdeyi
    tamamen belleğe alıyordu."""
    yanit = temiz.post(
        "/api/oturum/giris", json={"kullanici": "admin", "parola": "x" * 200_000}
    )
    assert yanit.status_code == 413
    assert "çok büyük" in yanit.json()["hata"].lower()


def test_makul_govde_gecer(temiz):
    assert temiz.giris().status_code == 200


def test_belge_ucu_gorsel_tasiyacak_kadar_comert(temiz):
    """Sınır, logo ve dokuz adım fotoğrafı taşıyan gerçek isteği engellememeli."""
    from ui.app import _govde_siniri

    assert _govde_siniri("/api/talimat") >= 64 * 1024 * 1024
    assert _govde_siniri("/api/oturum/giris") <= 64 * 1024


# --- Sıkıştırma bombası ------------------------------------------------------


def _sisirilmis_xlsx(tekrar: int) -> bytes:
    """Küçük görünen, açıldığında şişen bir xlsx üretir."""
    sisik = (
        '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org'
        '/spreadsheetml/2006/main">'
        + ('<si><t>' + "A" * 250 + '</t></si>') * tekrar
        + "</sst>"
    )
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("xl/sharedStrings.xml", sisik)
        z.writestr("xl/workbook.xml", "<workbook/>")
    return tampon.getvalue()


def test_sikistirma_bombasi_acilmadan_reddedilir():
    """455 KB'lik bir dosya 101 MB'a açılıyor ve tamamı ayrıştırılıyordu."""
    ham = _sisirilmis_xlsx(400_000)
    assert len(ham) < importers.MAKS_DOSYA_BOYUTU  # bayt sınırı bunu YAKALAMAZ

    with pytest.raises(GirdiHatasi) as hata:
        importers.oku("liste.xlsx", ham)
    metin = str(hata.value).lower()
    assert "sıkıştırılmış" in metin or "sınırın üstünde" in metin


def test_asiri_buyuk_dosya_reddedilir():
    with pytest.raises(GirdiHatasi) as hata:
        importers.oku("liste.csv", b"x" * (importers.MAKS_DOSYA_BOYUTU + 1))
    assert "çok büyük" in str(hata.value).lower()


def test_bos_dosya_reddedilir():
    with pytest.raises(GirdiHatasi):
        importers.oku("liste.csv", b"")


def test_normal_xlsx_hala_okunur():
    """Koruma, gerçek bir personel listesini engellememeli."""
    openpyxl = pytest.importorskip("openpyxl")

    kitap = openpyxl.Workbook()
    sayfa = kitap.active
    sayfa.append(["Ad Soyad", "Ünvan", "Telefon No"])
    sayfa.append(["MEHMET DEMİR", "OPERATÖR", "05001112233"])
    tampon = io.BytesIO()
    kitap.save(tampon)

    kayitlar = importers.oku("liste.xlsx", tampon.getvalue())
    assert len(kayitlar) == 1
    assert kayitlar[0].ad_soyad == "MEHMET DEMİR"


# --- Türkçe girdi ------------------------------------------------------------


def test_turkce_kimlik_bilgisi_cokme_uretmez(temiz):
    """hmac.compare_digest metinde ASCII dışı karakteri kabul etmez.

    Bayt yerine metin karşılaştırılırsa "müdür" yazan kullanıcı temiz bir
    401 yerine 500 alır. Türkçe konuşan bir fabrikada bu uç durum değildir.
    """
    for kullanici, parola in [("müdür", "admin"), ("admin", "şifre"), ("ŞEF", "İŞÇİ")]:
        yanit = temiz.post(
            "/api/oturum/giris", json={"kullanici": kullanici, "parola": parola}
        )
        assert yanit.status_code == 401, f"{kullanici}/{parola} -> {yanit.status_code}"


def test_turkce_parola_ayarlanabilir(monkeypatch, temiz):
    """KDU_PAROLA Türkçe karakter içerebilmeli."""
    monkeypatch.setenv("KDU_PAROLA", "çokGizliŞifre")
    assert guvenlik.dogrula("admin", "çokGizliŞifre") is True
    assert guvenlik.dogrula("admin", "admin") is False

