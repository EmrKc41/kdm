"""Form girdilerinin şablondan bağımsız veri modeli.

Bu sınıflar hem arayüzden gelen veriyi taşır hem de JSON "proje dosyası"
olarak diske yazılır. Şablon dosyalarına hiçbir referans içermezler; böylece
kullanıcı yarım kalan işine geri dönebilir.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .errors import GirdiHatasi

#: Doldurulmayan kontrol adımı bloğu için davranış.
BosBlok = Literal["cerceveli", "temizle"]

PROJE_SURUMU = 1


@dataclass
class KontrolAdimi:
    """İş talimatındaki tek bir kontrol adımı."""

    baslik: str = ""            # sarı alandaki KIRMIZI kalın başlık
    aciklama: str = ""          # sarı alandaki siyah açıklama
    cycle_sn: int | None = None
    gorsel: bytes | None = None
    gorsel_adi: str = ""

    @property
    def dolu(self) -> bool:
        return bool(
            self.baslik.strip()
            or self.aciklama.strip()
            or self.cycle_sn is not None
            or self.gorsel
        )


@dataclass
class TalimatVerisi:
    """FONKSİYON 1 — İş Talimatı girdileri."""

    # Başlık ve konu
    baslik: str = ""                      # A1:U4
    #: Başlık varsayılan olarak KULLANICININ YAZDIĞI GİBİ aktarılır.
    #: Otomatik büyütme kapalıdır çünkü Türkçe büyük harf kuralı 'i' harfini
    #: 'İ' yapar ve "Firewall" gibi yabancı kelimeleri "FİREWALL"a çevirir;
    #: şablondaki doğru yazım ise "FIREWALL"dur. Hangi kelimenin Türkçe
    #: olduğu programatik olarak bilinemeyeceği için karar kullanıcıya bırakılır.
    baslik_buyuk_harf: bool = False
    konu: str = ""                        # C5:W5 ham girdi
    konu_otomatik_ek: bool = True         # "<girdi> İŞ TALİMATI HK."

    # Sol üst kimlik bloğu
    parca_no: str = ""                    # C6:E6
    parca_adi: str = ""                   # C7:E7

    # Orta bloklar
    musteri: str = ""                     # J6:K6  "Bu işletme nereye üretiyor?"
    hazirlama_tarihi: str = ""            # J7:K7  GG.AA.YYYY
    hazirlayan: str = ""                  # N6:O6
    son_rev_tarihi: str = ""              # N7:O7  GG.AA.YYYY
    musteri_temsilcisi: str = ""          # R6:S6
    son_rev_aciklamasi: str = ""          # R7:S7
    onay: str = ""                        # V6:W6

    #: V7:W7 alanı ikonlarla kaplanır. `isg_ikonlari` doluysa bu metin
    #: YAZILMAZ (çakışma olurdu); yalnızca hiç ikon seçilmediğinde kullanılır.
    isg_ekipmani: str = ""
    #: core.isg_ikonlari.IKONLAR anahtarları — örn. ["baret", "eldiven"]
    isg_ikonlari: list[str] = field(default_factory=list)

    # Sağ üst doküman bloğu (V1:W4 — şablonda 8 ayrı hücre)
    sayfa_no: str = "1"
    talimat_no: str = ""
    rev_no: str = "0"
    tarih: str = ""                       # GG.AA.YYYY

    # Görseller
    # NOT: F6:G7'deki SC (özel karakteristik) sembolü şablonda sabittir ve
    # kullanıcıdan istenmez; bu yüzden burada bir parça görseli alanı yoktur.
    logo: bytes | None = None
    logo_adi: str = ""

    # Kontrol adımları — her zaman 9 elemanlı; boş olanlar üretilmez
    adimlar: list[KontrolAdimi] = field(
        default_factory=lambda: [KontrolAdimi() for _ in range(9)]
    )
    bos_blok_davranisi: BosBlok = "cerceveli"

    # --- Türetilmiş değerler -------------------------------------------------

    @property
    def konu_metni(self) -> str:
        """C5 hücresine yazılacak nihai konu metni."""
        ham = self.konu.strip()
        if not ham:
            return ""
        if self.konu_otomatik_ek and not ham.upper().endswith("HK."):
            return f"{ham} İŞ TALİMATI HK."
        return ham

    def dolu_adimlar(self) -> list[tuple[int, KontrolAdimi]]:
        """(0 tabanlı indeks, adım) çiftlerinden dolu olanlar."""
        return [(i, a) for i, a in enumerate(self.adimlar) if a.dolu]


@dataclass
class TneKatilimci:
    ad_soyad: str = ""
    sicil_no: str = ""


@dataclass
class TneVerisi:
    """FONKSİYON 2 — Tek Nokta Eğitimi girdileri."""

    baslik: str = ""
    konu: str = ""
    konu_otomatik_ek: bool = True

    mudurluk_birim: str = ""
    kisim: str = ""
    hazirlayan: str = ""

    parametre: str = ""
    olcum_araci: str = ""
    parca_etkisi: str = ""
    sorumlu: str = ""

    egitim_suresi: str = ""
    egitim_tarihi: str = ""
    tnd_no: str = ""
    egitim_veren: str = ""

    sayfa_no: str = "1/1"
    talimat_no: str = ""
    rev_no: str = "0"
    tarih: str = ""

    egitim_icerigi: list[str] = field(default_factory=list)   # GÜVENLİK, ÜRETİM, ...
    egitim_turu: list[str] = field(default_factory=list)      # TEMEL BİLGİ, ...

    logo: bytes | None = None
    logo_adi: str = ""
    egitim_gorseli: bytes | None = None
    egitim_gorseli_adi: str = ""

    katilimcilar: list[TneKatilimci] = field(default_factory=list)

    @property
    def konu_metni(self) -> str:
        ham = self.konu.strip()
        if not ham:
            return ""
        if self.konu_otomatik_ek and not ham.upper().endswith("HK."):
            return f"{ham} TEK NOKTA EĞİTİMİ HK."
        return ham


@dataclass
class HaftalikVardiya:
    """Üç vardiyanın TEK sayfada yan yana dizileceği haftalık çizelge.

    Sayfa adı tarihten türetilir: 17 Ağustos -> "Ağustos3.Hafta".
    """

    tarih: str = ""
    vardiyalar: list["VardiyaVerisi"] = field(default_factory=list)
    normal_unvanlar: list[str] = field(default_factory=lambda: ["Kalite Operatörü"])

    def __post_init__(self) -> None:
        # Tanınmayan harfli bir vardiya SESSİZCE ATILMAZ; hata verilir.
        # Aksi halde kullanıcının girdiği personel listesi yok olurdu.
        gecersiz = [
            v.vardiya_adi for v in self.vardiyalar if vardiya_harfi(v.vardiya_adi) is None
        ]
        if gecersiz:
            raise GirdiHatasi(
                f"Tanınmayan vardiya adı: {', '.join(repr(g) for g in gecersiz)}. "
                "Yalnızca " + ", ".join(VARDIYA_HARFLERI) + " kullanılabilir."
            )

        # Eksik vardiyalar boş olarak tamamlanır; sıra her zaman A, B, C.
        mevcut = {vardiya_harfi(v.vardiya_adi): v for v in self.vardiyalar}
        self.vardiyalar = [
            mevcut.get(h) or VardiyaVerisi(vardiya_adi=h, tarih=self.tarih)
            for h in VARDIYA_HARFLERI
        ]
        for v in self.vardiyalar:
            if not v.tarih.strip():
                v.tarih = self.tarih
            v.normal_unvanlar = self.normal_unvanlar

    @property
    def en_uzun_liste(self) -> int:
        return max((len(v.kayitlar) for v in self.vardiyalar), default=0)


@dataclass
class VardiyaKaydi:
    ad_soyad: str = ""
    unvan: str = ""
    calisma_yeri: str = ""
    telefon: str = ""
    durak: str = ""


@dataclass
class RaporSatiri:
    """Kalite uygunsuzluk takip raporundaki tek satır."""

    tanim: str = ""
    kok_neden: str = ""
    duzeltici_faaliyet: str = ""
    sorumlu: str = ""
    hedef_tarih: str = ""
    durum: str = ""

    @property
    def dolu(self) -> bool:
        return bool(
            self.tanim.strip()
            or self.kok_neden.strip()
            or self.duzeltici_faaliyet.strip()
            or self.sorumlu.strip()
            or self.hedef_tarih.strip()
            or self.durum.strip()
        )


@dataclass
class RaporVerisi:
    """FONKSİYON 4 — Kalite uygunsuzluk takip raporu girdileri."""

    baslik: str = "KALİTE UYGUNSUZLUK TAKİP RAPORU"
    konu: str = ""
    rapor_no: str = ""
    tarih: str = ""
    hazirlayan: str = ""
    genel_durum: str = "Açık"
    ozet: str = ""
    satirlar: list[RaporSatiri] = field(default_factory=list)


#: Vardiya harfi -> standart çalışma saati. Saatler harfle birlikte otomatik
#: belirlenir; kullanıcı isterse arayüzden yine de değiştirebilir.
VARDIYA_SAATLERI: dict[str, str] = {
    "A": "24.00 - 08.00",
    "B": "08.00 - 16.00",
    "C": "16.00 - 24.00",
}

VARDIYA_HARFLERI = tuple(VARDIYA_SAATLERI)


def vardiya_harfi(ad: str) -> str | None:
    """Serbest metinden vardiya harfini çıkarır; tanınmazsa None döner.

    "A", "a", "A VARDİYASI", "B-Vardiyası" gibi yazımların hepsi kabul edilir.
    "Gece" veya "D" gibi tanınmayan değerler None döner — çağıran taraf bunu
    sessizce yutmak yerine hata olarak bildirmelidir.
    """
    metin = (ad or "").strip()
    if not metin:
        return None

    harf = metin[0].upper()
    if harf not in VARDIYA_SAATLERI:
        return None
    # Harf tek başına bir sözcük olmalı. "A VARDİYASI" ve "B-Vardiyası"
    # kabul edilir; "Ağustos" edilmez — ikinci karakteri harf/rakamdır.
    if len(metin) > 1 and metin[1].isalnum():
        return None
    return harf


def vardiya_saati(harf: str) -> str:
    """Vardiya harfinin standart saat aralığını döndürür."""
    return VARDIYA_SAATLERI.get(vardiya_harfi(harf) or "", "")


@dataclass
class VardiyaVerisi:
    """FONKSİYON 3 — Tek bir vardiyanın listesi.

    Üç vardiya (A / B / C) arayüzde ayrı ayrı tutulur; her birinin kendi
    personel listesi vardır. Üretim, seçili vardiyanın verisiyle yapılır.
    """

    vardiya_adi: str = ""              # "A", "B" veya "C"
    tarih: str = ""
    vardiya_saati: str = ""            # boşsa harften otomatik türetilir
    kayitlar: list[VardiyaKaydi] = field(default_factory=list)

    #: Bu ünvanlar normal (siyah) yazılır; listede olmayan her ünvan
    #: KIRMIZI + KALIN olur. Kural motoru sabit kodlanmamıştır.
    normal_unvanlar: list[str] = field(default_factory=lambda: ["Kalite Operatörü"])

    def __post_init__(self) -> None:
        # Saat verilmediyse vardiya harfinden otomatik doldur.
        if not self.vardiya_saati.strip():
            self.vardiya_saati = vardiya_saati(self.vardiya_adi)

    @property
    def baslik(self) -> str:
        """Çıktının üst bloğunda görünecek tam ad.

        "A" -> "A VARDİYASI". Harf dışında serbest bir ad verilmişse
        OLDUĞU GİBİ kullanılır; büyük harfe çevrilmez, çünkü Python'un
        upper() metodu Türkçe'de 'i' harfini bozar.
        """
        harf = vardiya_harfi(self.vardiya_adi)
        if harf:
            return f"{harf} VARDİYASI"
        return self.vardiya_adi.strip() or "VARDİYA LİSTESİ"


# --- Proje dosyası (JSON) ----------------------------------------------------

_BINARY_ALANLAR = {"logo", "parca_gorseli", "gorsel", "egitim_gorseli"}


def proje_kaydet(veri: Any, yol: str | Path, tip: str) -> None:
    """Girdi verisini JSON proje dosyası olarak kaydeder.

    Görseller base64 olarak gömülür; proje dosyası tek başına taşınabilir.
    """
    govde = {
        "surum": PROJE_SURUMU,
        "tip": tip,
        "veri": _kodla(asdict(veri)),
    }
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(
        json.dumps(govde, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def proje_yukle(yol: str | Path) -> tuple[str, dict]:
    """Proje dosyasını okur, (tip, sözlük) döndürür."""
    yol = Path(yol)
    try:
        govde = json.loads(yol.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GirdiHatasi(f"Proje dosyası bulunamadı: {yol.name}") from exc
    except json.JSONDecodeError as exc:
        raise GirdiHatasi(
            f"'{yol.name}' geçerli bir proje dosyası değil veya bozulmuş."
        ) from exc

    if govde.get("surum") != PROJE_SURUMU:
        raise GirdiHatasi(
            "Proje dosyası bu sürümle uyumlu değil. "
            f"Beklenen sürüm {PROJE_SURUMU}, dosyadaki {govde.get('surum')}."
        )
    return govde.get("tip", ""), _coz(govde.get("veri", {}))


def _kodla(o: Any) -> Any:
    if isinstance(o, dict):
        return {
            k: (
                base64.b64encode(v).decode("ascii")
                if k in _BINARY_ALANLAR and isinstance(v, bytes)
                else _kodla(v)
            )
            for k, v in o.items()
        }
    if isinstance(o, list):
        return [_kodla(v) for v in o]
    return o


def _coz(o: Any) -> Any:
    if isinstance(o, dict):
        return {
            k: (
                base64.b64decode(v)
                if k in _BINARY_ALANLAR and isinstance(v, str) and v
                else _coz(v)
            )
            for k, v in o.items()
        }
    if isinstance(o, list):
        return [_coz(v) for v in o]
    return o
