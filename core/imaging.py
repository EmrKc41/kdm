"""Görsel hazırlama: en-boy oranını koruyarak hedef kutuya sığdırma.

Görev tanımı gereği görseller KIRPILMAZ. Hedef kutuya oranı bozulmadan
sığdırılır ve artan alan beyaz dolgu ile doldurularak görsel ortalanır.
Böylece çıktıdaki `<xdr:ext>` her zaman istenen tam EMU değerine eşit olur.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .errors import GorselHatasi
from .units import EMU_PER_PIXEL

#: Kabul edilen yükleme biçimleri.
KABUL_EDILEN_UZANTILAR = {".png", ".jpg", ".jpeg", ".svg"}

#: Tek bir görsel için üst sınır (bayt).
MAKS_GORSEL_BOYUTU = 20 * 1024 * 1024

#: Tek bir görsel için üst piksel sınırı (genişlik x yükseklik).
#:
#: Bayt sınırı tek başına yetmez: düz renkli 12000x12000 bir PNG diskte
#: 0,4 MB'dir ama açıldığında ~430 MB bellek ister. Tek istekte logo ve
#: dokuz adım fotoğrafı birden gelebildiği için bu, fabrika makinesinde
#: belleği tüketir. Pillow'un kendi savunması 89 megapikselde yalnızca
#: UYARI verir, hata değil; bu yüzden sınır burada açıkça konur.
#: 60 MP, 8K bir fotoğraf makinesi çıktısının çok üstündedir.
MAKS_PIKSEL = 60_000_000

#: Çıktı çözünürlüğünü sınırlamak için ölçek çarpanı. Kutu boyutunun bu katı
#: kadar piksel üretilir; 2 = retina keskinliği, makul dosya boyutu.
OLCEK = 2


#: Dosya uzantısından Pillow biçim adına eşleme. Bir medya parçasının
#: üzerine yazarken içerik ile uzantı UYUŞMALIDIR; aksi halde paket
#: [Content_Types] bildirimiyle çelişir.
UZANTI_BICIM = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
}


def bicim_sec(dosya_adi: str) -> str:
    """Bir medya parçası adına uygun Pillow biçimini döndürür."""
    return UZANTI_BICIM.get(Path(dosya_adi).suffix.lower(), "PNG")


def _olcu_dogrula(olcu: tuple[int, int]) -> None:
    """Açılan görselin piksel sayısını sınıra karşı denetler."""
    piksel = olcu[0] * olcu[1]
    if piksel > MAKS_PIKSEL:
        raise GorselHatasi(
            f"Görsel çok büyük: {olcu[0]}x{olcu[1]} piksel "
            f"({piksel / 1_000_000:.0f} MP). En fazla "
            f"{MAKS_PIKSEL // 1_000_000} MP kabul edilir. "
            "Görseli küçültüp tekrar yükleyin."
        )


def hazirla(
    kaynak: bytes | str | Path,
    hedef_genislik_emu: int,
    hedef_yukseklik_emu: int,
    *,
    arka_plan: tuple[int, int, int] = (255, 255, 255),
    bicim: str = "PNG",
) -> bytes:
    """Görseli hedef kutuya sığdırıp istenen biçimde bayt olarak döndürür.

    `kaynak` ham bayt veya dosya yolu olabilir.
    """
    veri = _oku(kaynak)

    if len(veri) > MAKS_GORSEL_BOYUTU:
        mb = MAKS_GORSEL_BOYUTU // (1024 * 1024)
        raise GorselHatasi(
            f"Görsel çok büyük: {len(veri) / 1024 / 1024:.1f} MB. "
            f"En fazla {mb} MB kabul edilir."
        )

    try:
        img = Image.open(io.BytesIO(veri))
        # Ölçü denetimi load() ÖNCESİNDE yapılır: Image.open yalnızca
        # başlığı okur, belleği asıl ayıran load()'dur. Sonra bakmak,
        # korunmak istenen tahsisi zaten yapmış olmak demektir.
        _olcu_dogrula(img.size)
        img.load()
    except UnidentifiedImageError as exc:
        raise GorselHatasi(
            "Görsel tanınamadı. Lütfen PNG veya JPG biçiminde bir dosya yükleyin."
        ) from exc
    except GorselHatasi:
        # Ölçü denetiminin anlaşılır mesajı, aşağıdaki genel yakalamaya
        # düşerse "dosya bozuk olabilir" diye yanlış bir mesaja dönüşür.
        raise
    except Exception as exc:
        raise GorselHatasi("Görsel açılamadı, dosya bozuk olabilir.") from exc

    hedef_w = max(1, int(round(hedef_genislik_emu / EMU_PER_PIXEL * OLCEK)))
    hedef_h = max(1, int(round(hedef_yukseklik_emu / EMU_PER_PIXEL * OLCEK)))

    img = _duzlestir(img, arka_plan)

    oran = min(hedef_w / img.width, hedef_h / img.height)
    yeni_w = max(1, int(round(img.width * oran)))
    yeni_h = max(1, int(round(img.height * oran)))
    kucultulmus = img.resize((yeni_w, yeni_h), Image.LANCZOS)

    tuval = Image.new("RGB", (hedef_w, hedef_h), arka_plan)
    tuval.paste(kucultulmus, ((hedef_w - yeni_w) // 2, (hedef_h - yeni_h) // 2))

    cikti = io.BytesIO()
    if bicim.upper() == "JPEG":
        tuval.save(cikti, format="JPEG", quality=92, optimize=True)
    else:
        tuval.save(cikti, format="PNG", optimize=True)
    return cikti.getvalue()


def dogrula(dosya_adi: str, veri: bytes) -> None:
    """Yüklemeyi kabul etmeden önce tip ve boyut denetimi yapar."""
    uzanti = Path(dosya_adi).suffix.lower()
    if uzanti not in KABUL_EDILEN_UZANTILAR:
        kabul = ", ".join(sorted(KABUL_EDILEN_UZANTILAR))
        raise GorselHatasi(
            f"'{dosya_adi}' desteklenmeyen bir dosya tipi. Kabul edilenler: {kabul}"
        )
    if len(veri) > MAKS_GORSEL_BOYUTU:
        mb = MAKS_GORSEL_BOYUTU // (1024 * 1024)
        raise GorselHatasi(
            f"'{dosya_adi}' çok büyük. Görsel boyutu en fazla {mb} MB olabilir."
        )
    if not veri:
        raise GorselHatasi(f"'{dosya_adi}' boş görünüyor.")


def _oku(kaynak: bytes | str | Path) -> bytes:
    if isinstance(kaynak, bytes):
        return kaynak
    yol = Path(kaynak)
    if not yol.is_file():
        raise GorselHatasi(f"Görsel dosyası bulunamadı: {yol.name}")
    return yol.read_bytes()


def _duzlestir(img: Image.Image, arka_plan: tuple[int, int, int]) -> Image.Image:
    """Saydam görselleri beyaz zemine yerleştirerek RGB'ye çevirir."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        zemin = Image.new("RGB", rgba.size, arka_plan)
        zemin.paste(rgba, mask=rgba.split()[-1])
        return zemin
    return img.convert("RGB")
