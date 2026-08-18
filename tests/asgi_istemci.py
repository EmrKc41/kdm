"""Bağımlılıksız minimal ASGI test istemcisi.

`fastapi.testclient.TestClient` httpx gerektirir. Bu proje internetsiz bir
fabrika makinesine kurulacağı için ek bağımlılık istemiyoruz; uygulamayı
doğrudan ASGI arayüzünden çağıran küçük bir istemci yeterli.
"""

from __future__ import annotations

import asyncio
import json as jsonlib
from dataclasses import dataclass, field
from urllib.parse import urlsplit


@dataclass
class Yanit:
    status_code: int
    headers: dict[str, str]
    content: bytes = b""

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")

    def json(self):
        return jsonlib.loads(self.text)


@dataclass
class AsgiIstemci:
    """Çerez taşıyan minimal istemci.

    Motor oturum çerezi kullandığı için istemcinin de basit bir çerez kavanozu
    olmalı; aksi halde her istek 401 döner. Kavanoz bilinçli olarak naiftir:
    alan adı, yol ve son kullanma denetimi yapılmaz, çünkü testler tek bir
    uygulamayla konuşur.
    """

    app: object
    cerezler: dict[str, str] = field(default_factory=dict)
    _dongu: asyncio.AbstractEventLoop = field(default=None, repr=False)

    def __post_init__(self):
        self._dongu = asyncio.new_event_loop()

    def giris(self, kullanici: str = "admin", parola: str = "admin") -> Yanit:
        """Testlerin çoğu oturum açmış bir kullanıcıyı varsayar."""
        return self.post(
            "/api/oturum/giris", json={"kullanici": kullanici, "parola": parola}
        )

    def get(self, yol: str) -> Yanit:
        return self._istek("GET", yol, None)

    def post(self, yol: str, json=None) -> Yanit:
        return self._istek("POST", yol, json)

    def _istek(self, yontem: str, yol: str, json) -> Yanit:
        parcali = urlsplit(yol)
        govde = jsonlib.dumps(json).encode("utf-8") if json is not None else b""

        basliklar = [(b"host", b"testserver")]
        if self.cerezler:
            cerez = "; ".join(f"{a}={d}" for a, d in self.cerezler.items())
            basliklar.append((b"cookie", cerez.encode()))
        if json is not None:
            basliklar += [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(govde)).encode()),
            ]

        kapsam = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": yontem,
            "scheme": "http",
            "path": parcali.path,
            "raw_path": parcali.path.encode(),
            "query_string": parcali.query.encode(),
            "root_path": "",
            "headers": basliklar,
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
        }

        gonderilenler: list[dict] = []
        alindi = {"deger": False}

        async def al():
            if alindi["deger"]:
                return {"type": "http.disconnect"}
            alindi["deger"] = True
            return {"type": "http.request", "body": govde, "more_body": False}

        async def gonder(mesaj):
            gonderilenler.append(mesaj)

        self._dongu.run_until_complete(self.app(kapsam, al, gonder))

        durum, basliklar_cikti, icerik = 500, {}, b""
        ham_basliklar: list[tuple[bytes, bytes]] = []
        for m in gonderilenler:
            if m["type"] == "http.response.start":
                durum = m["status"]
                ham_basliklar = m.get("headers", [])
                basliklar_cikti = {
                    k.decode().lower(): v.decode() for k, v in ham_basliklar
                }
            elif m["type"] == "http.response.body":
                icerik += m.get("body", b"")

        # Set-Cookie birden çok kez gelebileceği için ham listeden okunur;
        # sözlüğe indirgenmiş başlıklarda yalnızca sonuncusu kalırdı.
        for anahtar, deger in ham_basliklar:
            if anahtar.decode().lower() != "set-cookie":
                continue
            ikili = deger.decode().split(";", 1)[0]
            ad, _, veri = ikili.partition("=")
            if not veri or 'Max-Age=0' in deger.decode():
                self.cerezler.pop(ad.strip(), None)
            else:
                self.cerezler[ad.strip()] = veri

        return Yanit(durum, basliklar_cikti, icerik)
