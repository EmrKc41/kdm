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
    app: object
    _dongu: asyncio.AbstractEventLoop = field(default=None, repr=False)

    def __post_init__(self):
        self._dongu = asyncio.new_event_loop()

    def get(self, yol: str) -> Yanit:
        return self._istek("GET", yol, None)

    def post(self, yol: str, json=None) -> Yanit:
        return self._istek("POST", yol, json)

    def _istek(self, yontem: str, yol: str, json) -> Yanit:
        parcali = urlsplit(yol)
        govde = jsonlib.dumps(json).encode("utf-8") if json is not None else b""

        basliklar = [(b"host", b"testserver")]
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
        for m in gonderilenler:
            if m["type"] == "http.response.start":
                durum = m["status"]
                basliklar_cikti = {
                    k.decode().lower(): v.decode() for k, v in m.get("headers", [])
                }
            elif m["type"] == "http.response.body":
                icerik += m.get("body", b"")

        return Yanit(durum, basliklar_cikti, icerik)
