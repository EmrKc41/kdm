import io
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

SABLON_TALIMAT = KOK / "templates" / "taslaktalimat.xlsx"
SABLON_TNE = KOK / "templates" / "taslaktne.xlsx"

#: Şablonlar depoda TUTULMAZ: bir firmanın gerçek kalite dokümanlarıdır.
#: Kullanıcı kendi `templates/` klasörünü doldurur. Bu yüzden şablona
#: bağlı testler, dosyalar yoksa düşmez — atlanır. Aksi halde depoyu
#: klonlayan herkes kırmızı bir test takımı görürdü.
SABLONLAR_VAR = SABLON_TALIMAT.is_file() and SABLON_TNE.is_file()

sablon_gerekir = pytest.mark.skipif(
    not SABLONLAR_VAR,
    reason="templates/ altında şablon yok (depoda tutulmuyor)",
)


@pytest.fixture(scope="session")
def sablon_talimat() -> Path:
    if not SABLON_TALIMAT.is_file():
        pytest.skip("taslaktalimat.xlsx bulunamadı")
    return SABLON_TALIMAT


@pytest.fixture(scope="session")
def sablon_tne() -> Path:
    if not SABLON_TNE.is_file():
        pytest.skip("taslaktne.xlsx bulunamadı")
    return SABLON_TNE


@pytest.fixture
def gorsel_uret():
    """Belirtilen ölçüde test görseli üretir."""

    def _uret(genislik: int = 800, yukseklik: int = 300, renk=(230, 235, 245)) -> bytes:
        img = Image.new("RGB", (genislik, yukseklik), renk)
        d = ImageDraw.Draw(img)
        d.rectangle([1, 1, genislik - 2, yukseklik - 2], outline=(40, 40, 40), width=2)
        tampon = io.BytesIO()
        img.save(tampon, "PNG")
        return tampon.getvalue()

    return _uret


@pytest.fixture
def ornek_talimat(gorsel_uret):
    """Dolu bir İş Talimatı veri seti."""
    from core.models import KontrolAdimi, TalimatVerisi

    veri = TalimatVerisi(
        baslik="FIREWALL İŞ TALİMATI",
        konu="10598-AG",
        parca_no="10598-AG",
        parca_adi="FIREWALL SAĞ",
        musteri="FORD OTOSAN — GÖLCÜK",
        hazirlama_tarihi="17.08.2026",
        hazirlayan="Emirhan Koç",
        son_rev_tarihi="17.08.2026",
        musteri_temsilcisi="Şükrü Güngör",
        son_rev_aciklamasi="İlk yayın",
        onay="Kalite Müdürü",
        isg_ekipmani="Eldiven, Gözlük, Baret",
        talimat_no="BC-F-0139",
        tarih="17.08.2026",
        logo=gorsel_uret(600, 280),
        isg_ikonlari=["baret", "gozluk", "eldiven", "ayakkabi"],
    )
    for i in range(9):
        veri.adimlar[i] = KontrolAdimi(
            baslik=f"{i + 1}. ADIM KONTROLÜ",
            aciklama="Kaynak dikişi gözle kontrol edilir.",
            cycle_sn=3 + i,
            gorsel=gorsel_uret(1400, 400),
        )
    return veri
