"""Motor tarafı oturum doğrulamasının testleri.

Arayüzdeki giriş ekranı yalnızca bir kilittir; asıl koruma buradadır. Bu
testler, motorun oturumsuz isteği gerçekten reddettiğini doğrular — arayüz
atlanıp uçlar doğrudan çağrıldığında da.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from tests.asgi_istemci import AsgiIstemci      # noqa: E402
from ui import guvenlik                         # noqa: E402
from ui.app import app                          # noqa: E402


@pytest.fixture
def temiz():
    """Her test kendi istemcisiyle, boş jeton deposundan başlar."""
    guvenlik.hepsini_sil()
    yield AsgiIstemci(app)
    guvenlik.hepsini_sil()


def test_oturumsuz_belge_uretimi_reddedilir(temiz):
    yanit = temiz.post("/api/talimat", json={"baslik": "KAÇAK"})
    assert yanit.status_code == 401
    assert "giriş" in yanit.json()["hata"].lower()


def test_oturumsuz_ayar_okuma_reddedilir(temiz):
    assert temiz.get("/api/ayarlar/unvanlar").status_code == 401
    assert temiz.get("/api/isg-ikonlari").status_code == 401


def test_saglik_ucu_oturumsuz_da_calisir(temiz):
    """Giriş ekranı motorun ayakta olduğunu göstermek zorunda; kapalıysa
    kullanıcı boşuna parola dener."""
    yanit = temiz.get("/api/health")
    assert yanit.status_code == 200
    assert yanit.json()["durum"] == "acik"


def test_yanlis_parola_reddedilir(temiz):
    yanit = temiz.post(
        "/api/oturum/giris", json={"kullanici": "admin", "parola": "yanlis"}
    )
    assert yanit.status_code == 401
    # Hangi alanın hatalı olduğu sızdırılmamalı.
    metin = yanit.json()["hata"].lower()
    assert "kullanıcı adı veya parola" in metin


def test_yanlis_kullanici_ayni_mesaji_verir(temiz):
    a = temiz.post("/api/oturum/giris", json={"kullanici": "baskasi", "parola": "admin"})
    b = temiz.post("/api/oturum/giris", json={"kullanici": "admin", "parola": "yanlis"})
    assert a.json()["hata"] == b.json()["hata"]


def test_giris_sonrasi_uretim_calisir(temiz):
    assert temiz.giris().status_code == 200
    yanit = temiz.post("/api/talimat", json={"baslik": "OTURUMLU TALİMAT"})
    assert yanit.status_code == 200


def test_kullanici_adi_buyuk_harfle_de_kabul_edilir(temiz):
    """Türkçe küçültme burada YANLIŞ olurdu: "ADMIN" → "admın"."""
    assert temiz.giris("ADMIN", "admin").status_code == 200


def test_cikis_oturumu_kapatir(temiz):
    temiz.giris()
    assert temiz.get("/api/oturum/durum").json()["acik"] is True

    assert temiz.post("/api/oturum/cikis").status_code == 200
    assert temiz.get("/api/oturum/durum").json()["acik"] is False
    assert temiz.post("/api/talimat", json={"baslik": "X"}).status_code == 401


def test_cerez_httponly_ve_samesite_tasir(temiz):
    yanit = temiz.giris()
    cerez = yanit.headers["set-cookie"].lower()
    # HttpOnly: sayfadaki JavaScript jetonu okuyamaz.
    assert "httponly" in cerez
    assert "samesite=lax" in cerez


def test_gecersiz_jeton_kabul_edilmez(temiz):
    temiz.giris()
    temiz.cerezler[guvenlik.CEREZ] = "uydurma-jeton"
    assert temiz.post("/api/talimat", json={"baslik": "X"}).status_code == 401
