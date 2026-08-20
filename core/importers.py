"""Toplu giriş: CSV ve Excel dosyasından vardiya kaydı içe aktarma (3.1).

Sütun başlıkları esnek eşleştirilir: büyük/küçük harf, Türkçe karakter ve
noktalama farkları göz ardı edilir. Böylece kullanıcı kendi listesini
yeniden düzenlemeden yükleyebilir.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .errors import GirdiHatasi
from .models import VardiyaKaydi
from .naming import guvenli

#: Her alan için kabul edilen başlık varyantları.
BASLIK_ESLEME = {
    "ad_soyad": ["ad soyad", "adsoyad", "ad", "isim", "ad_soyad", "personel", "ad soyadi"],
    "unvan": ["unvan", "ünvan", "gorev", "görev", "pozisyon"],
    "calisma_yeri": [
        "calisacagi yer", "çalışacağı yer", "calisma yeri", "çalışma yeri",
        "yer", "hat", "calisacagi yer hat", "çalışacağı yer / hat", "bolum", "bölüm",
    ],
    "telefon": ["telefon", "telefon no", "tel", "gsm", "cep", "telefon numarasi"],
    "durak": ["durak", "durak ismi", "durak adi", "durak adı", "servis", "servis duragi"],
}

#: Excel'in bilimsel gösterime çevirdiği telefonları toparlamak için.
MAKS_SATIR = 5000

#: Yüklenen dosya için üst sınır (bayt).
MAKS_DOSYA_BOYUTU = 10 * 1024 * 1024

#: xlsx açıldığında izin verilen toplam açılmış boyut (bayt).
#:
#: Bayt sınırı tek başına YETMEZ: xlsx bir ZIP arşividir ve yüksek
#: sıkıştırılabilir içerik küçük görünür. Ölçüldü — 455 KB'lik bir dosya
#: openpyxl'e verildiğinde 101 MB'lık paylaşılan metin tablosuna açılıyor
#: ve tamamı belleğe alınıyordu; `read_only` ve `MAKS_SATIR` bunu
#: sınırlamaz, çünkü sharedStrings sayfadan önce bütün olarak okunur.
MAKS_ACILMIS_BOYUT = 60 * 1024 * 1024

#: İzin verilen azami sıkıştırma oranı. Normal bir xlsx 5-20 kat sıkışır;
#: 200 kat, kasıtlı olarak şişirilmiş içeriğin işaretidir.
MAKS_SIKISTIRMA_ORANI = 200


def _normalize(baslik: str) -> str:
    return guvenli(str(baslik or "")).replace("_", " ").strip().lower()


def _sutun_haritasi(basliklar: list[str]) -> dict[str, int]:
    """Dosyadaki başlıkları model alanlarına eşler."""
    harita: dict[str, int] = {}
    normalize = [_normalize(b) for b in basliklar]

    for alan, varyantlar in BASLIK_ESLEME.items():
        hedefler = {_normalize(v) for v in varyantlar}
        for i, b in enumerate(normalize):
            if b in hedefler:
                harita[alan] = i
                break
    return harita


def _satirlardan_kayitlar(satirlar: list[list[str]]) -> list[VardiyaKaydi]:
    if not satirlar:
        raise GirdiHatasi("Dosya boş görünüyor.")

    harita = _sutun_haritasi(satirlar[0])
    if "ad_soyad" not in harita:
        bulunan = ", ".join(str(b) for b in satirlar[0] if str(b).strip())
        raise GirdiHatasi(
            "Dosyada 'Ad Soyad' sütunu bulunamadı. "
            f"Okunan başlıklar: {bulunan or '(boş)'}. "
            "Beklenen sütunlar: Ad Soyad, Ünvan, Çalışacağı Yer, Telefon No, Durak İsmi."
        )

    kayitlar: list[VardiyaKaydi] = []
    for satir in satirlar[1 : MAKS_SATIR + 1]:
        def al(alan: str) -> str:
            i = harita.get(alan)
            if i is None or i >= len(satir):
                return ""
            return str(satir[i] if satir[i] is not None else "").strip()

        ad = al("ad_soyad")
        if not ad:
            continue
        kayitlar.append(
            VardiyaKaydi(
                ad_soyad=ad,
                unvan=al("unvan"),
                calisma_yeri=al("calisma_yeri"),
                telefon=_telefon_duzelt(al("telefon")),
                durak=al("durak"),
            )
        )

    if not kayitlar:
        raise GirdiHatasi("Dosyada okunabilir kayıt bulunamadı.")
    return kayitlar


def _telefon_duzelt(deger: str) -> str:
    """Excel'in sayıya çevirdiği telefonları okunur hale getirir.

    Baştaki sıfır kaybolmuşsa geri eklenmez (uydurma veri üretilmez), ancak
    '5.32e+09' gibi bilimsel gösterim ve sondaki '.0' temizlenir.
    """
    deger = deger.strip()
    if deger.endswith(".0"):
        deger = deger[:-2]
    if "e+" in deger.lower():
        try:
            deger = f"{int(float(deger))}"
        except ValueError:
            pass
    return deger


def csvden_oku(veri: bytes | str, dosya_adi: str = "liste.csv") -> list[VardiyaKaydi]:
    """CSV içeriğinden kayıt listesi üretir. Ayraç otomatik saptanır."""
    if isinstance(veri, bytes):
        metin = _coz(veri, dosya_adi)
    else:
        metin = veri

    ornek = metin[:4096]
    try:
        ayrac = csv.Sniffer().sniff(ornek, delimiters=";,\t|").delimiter
    except csv.Error:
        ayrac = ";" if ornek.count(";") > ornek.count(",") else ","

    satirlar = [s for s in csv.reader(io.StringIO(metin), delimiter=ayrac) if any(s)]
    return _satirlardan_kayitlar(satirlar)


def exceldan_oku(veri: bytes | str | Path) -> list[VardiyaKaydi]:
    """Excel dosyasının ilk sayfasından kayıt listesi üretir."""
    import openpyxl

    kaynak = io.BytesIO(veri) if isinstance(veri, bytes) else veri
    try:
        wb = openpyxl.load_workbook(kaynak, data_only=True, read_only=True)
    except Exception as exc:
        raise GirdiHatasi(
            "Excel dosyası okunamadı. Dosyanın .xlsx biçiminde ve bozuk "
            "olmadığından emin olun."
        ) from exc

    ws = wb.worksheets[0]
    satirlar = [
        ["" if h is None else str(h) for h in satir]
        for satir in ws.iter_rows(values_only=True, max_row=MAKS_SATIR + 1)
        if any(h is not None and str(h).strip() for h in satir)
    ]
    wb.close()
    return _satirlardan_kayitlar(satirlar)


def _boyut_dogrula(veri: bytes, dosya_adi: str) -> None:
    if len(veri) > MAKS_DOSYA_BOYUTU:
        mb = MAKS_DOSYA_BOYUTU // (1024 * 1024)
        raise GirdiHatasi(
            f"'{dosya_adi}' çok büyük ({len(veri) / 1024 / 1024:.1f} MB). "
            f"En fazla {mb} MB kabul edilir."
        )
    if not veri:
        raise GirdiHatasi(f"'{dosya_adi}' boş görünüyor.")


def _zip_bombasi_mi(veri: bytes, dosya_adi: str) -> None:
    """xlsx'i açmadan ÖNCE arşivin açılmış boyutunu denetler.

    openpyxl'e verilen dosya, açıldığında belleğe sığmayacak kadar büyük
    olabilir. Arşiv dizini gerçek okuma yapmadan boyutları bildirir; bu
    yüzden denetim ucuzdur ve zararlı içerik hiç ayrıştırılmaz.
    """
    import zipfile

    try:
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            acilmis = sum(bilgi.file_size for bilgi in z.infolist())
    except zipfile.BadZipFile as exc:
        raise GirdiHatasi(
            f"'{dosya_adi}' geçerli bir Excel dosyası değil."
        ) from exc

    if acilmis > MAKS_ACILMIS_BOYUT:
        raise GirdiHatasi(
            f"'{dosya_adi}' açıldığında {acilmis / 1024 / 1024:.0f} MB yer "
            f"kaplıyor; bu sınırın üstünde. Dosyayı Excel'de açıp yalnızca "
            "personel listesini içeren yeni bir dosya olarak kaydedin."
        )

    oran = acilmis / max(len(veri), 1)
    if oran > MAKS_SIKISTIRMA_ORANI:
        raise GirdiHatasi(
            f"'{dosya_adi}' olağandışı biçimde sıkıştırılmış "
            f"({oran:.0f} kat). Dosya bozuk veya kasıtlı olarak şişirilmiş "
            "olabilir; güvenlik gereği okunmadı."
        )


def oku(dosya_adi: str, veri: bytes) -> list[VardiyaKaydi]:
    """Uzantıya göre doğru okuyucuyu seçer."""
    _boyut_dogrula(veri, dosya_adi)
    uzanti = Path(dosya_adi).suffix.lower()
    if uzanti in (".csv", ".txt"):
        return csvden_oku(veri, dosya_adi)
    if uzanti in (".xlsx", ".xlsm"):
        _zip_bombasi_mi(veri, dosya_adi)
        return exceldan_oku(veri)
    raise GirdiHatasi(
        f"'{dosya_adi}' desteklenmeyen bir dosya tipi. "
        "CSV (.csv) veya Excel (.xlsx) yükleyin."
    )


def _coz(veri: bytes, dosya_adi: str) -> str:
    """Türkçe CSV'lerde sık görülen kodlamaları sırayla dener."""
    for kodlama in ("utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin-1"):
        try:
            return veri.decode(kodlama)
        except UnicodeDecodeError:
            continue
    raise GirdiHatasi(
        f"'{dosya_adi}' dosyasının karakter kodlaması çözülemedi. "
        "Dosyayı UTF-8 olarak kaydedip tekrar deneyin."
    )
