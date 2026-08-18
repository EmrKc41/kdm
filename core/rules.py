"""Biçimlendirme kural motoru.

Görev tanımı 3.2: "Bu kural, ünvan listesi ayarlar ekranından genişletilebilir
olsun; kural motoru sabit kodlanmasın."

Kurallar veri olarak tanımlanır ve JSON'dan yüklenip kaydedilebilir. Kod
yalnızca kuralları DEĞERLENDİRİR; hangi ünvanın hangi biçimi alacağını bilmez.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import GirdiHatasi
from .textutil import kucult


@dataclass
class KayitBicimi:
    """Bir satıra uygulanacak görsel biçim."""

    kalin: bool = False
    renk: str = "000000"          # 6 haneli RGB
    italik: bool = False

    def birlestir(self, digeri: "KayitBicimi") -> "KayitBicimi":
        return KayitBicimi(
            kalin=self.kalin or digeri.kalin,
            renk=digeri.renk if digeri.renk != "000000" else self.renk,
            italik=self.italik or digeri.italik,
        )


#: Desteklenen karşılaştırma operatörleri.
OPERATORLER = ("listede", "listede_degil", "esittir", "icerir", "bos")


@dataclass
class BicimKurali:
    """Tek bir koşul → biçim eşlemesi."""

    ad: str
    alan: str                              # VardiyaKaydi alan adı, örn. "unvan"
    operator: str                          # OPERATORLER içinden
    degerler: list[str] = field(default_factory=list)
    bicim: KayitBicimi = field(default_factory=KayitBicimi)
    etkin: bool = True

    def uyuyor_mu(self, kayit: Any) -> bool:
        if not self.etkin:
            return False

        ham = str(getattr(kayit, self.alan, "") or "")
        deger = kucult(ham.strip())
        liste = [kucult(d.strip()) for d in self.degerler]

        if self.operator == "listede":
            return deger in liste
        if self.operator == "listede_degil":
            return bool(deger) and deger not in liste
        if self.operator == "esittir":
            return bool(liste) and deger == liste[0]
        if self.operator == "icerir":
            return any(d in deger for d in liste if d)
        if self.operator == "bos":
            return not deger
        raise GirdiHatasi(
            f"'{self.operator}' tanınmayan bir kural operatörü. "
            "Geçerli olanlar: " + ", ".join(OPERATORLER)
        )


class KuralMotoru:
    """Kural listesini sırayla değerlendirir; ilk uyan kural kazanır."""

    def __init__(
        self,
        kurallar: list[BicimKurali] | None = None,
        varsayilan: KayitBicimi | None = None,
    ):
        self.kurallar = kurallar if kurallar is not None else varsayilan_kurallar()
        self.varsayilan = varsayilan or KayitBicimi()

    def bicim(self, kayit: Any) -> KayitBicimi:
        for kural in self.kurallar:
            if kural.uyuyor_mu(kayit):
                return kural.bicim
        return self.varsayilan

    # --- Kalıcılık -----------------------------------------------------------

    def kaydet(self, yol: str | Path) -> None:
        govde = {
            "varsayilan": asdict(self.varsayilan),
            "kurallar": [asdict(k) for k in self.kurallar],
        }
        Path(yol).write_text(
            json.dumps(govde, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def yukle(cls, yol: str | Path) -> "KuralMotoru":
        try:
            govde = json.loads(Path(yol).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError as exc:
            raise GirdiHatasi(
                f"Kural dosyası okunamadı, biçimi bozuk: {Path(yol).name}"
            ) from exc

        kurallar = [
            BicimKurali(
                ad=k.get("ad", "Adsız kural"),
                alan=k.get("alan", "unvan"),
                operator=k.get("operator", "listede_degil"),
                degerler=list(k.get("degerler", [])),
                bicim=KayitBicimi(**k.get("bicim", {})),
                etkin=k.get("etkin", True),
            )
            for k in govde.get("kurallar", [])
        ]
        return cls(kurallar, KayitBicimi(**govde.get("varsayilan", {})))


def varsayilan_kurallar(normal_unvanlar: list[str] | None = None) -> list[BicimKurali]:
    """Görev tanımındaki 3.2 kuralının veri olarak ifadesi.

    Ünvanı listede OLMAYAN herkes (Sorumlu, Formen, Şef, Mühendis vb.)
    kırmızı ve kalın; listedekiler siyah ve normal.
    """
    return [
        BicimKurali(
            ad="Kalite Operatörü dışındaki ünvanlar vurgulanır",
            alan="unvan",
            operator="listede_degil",
            degerler=list(normal_unvanlar or ["Kalite Operatörü"]),
            bicim=KayitBicimi(kalin=True, renk="C00000"),
        )
    ]
