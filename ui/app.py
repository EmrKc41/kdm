"""Yerel web arayüzü (FastAPI).

TASARIM KARARLARI
    * Fabrika ortamında İNTERNETSİZ çalışır: hiçbir CDN, uzak font veya
      uzak betik kullanılmaz. Kök yol (/) yalnızca Next.js arayüzüne
      yönlendiren ince bir bilgi sayfasıdır; birincil arayüz :3000'dedir.
    * Görseller çok parçalı (multipart) yükleme yerine JSON içinde base64
      olarak taşınır. Böylece `python-multipart` ve `jinja2` bağımlılıkları
      gerekmez; kurulum yükü azalır ve veri modeli proje dosyasıyla aynı olur.
    * Kullanıcıya asla teknik hata izi gösterilmez; her hata anlaşılır
      Türkçe mesaja çevrilir.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from ui import guvenlik                                              # noqa: E402
from core import importers, isg_ikonlari, naming                     # noqa: E402
from core.tarih import hafta_adi                                     # noqa: E402
from core.errors import UygulamaHatasi                               # noqa: E402
from core.generators import talimat, tne, vardiya, rapor                    # noqa: E402
from core.models import (                                            # noqa: E402
    VARDIYA_SAATLERI,
    HaftalikVardiya,
    KontrolAdimi,
    TalimatVerisi,
    TneKatilimci,
    TneVerisi,
    RaporSatiri,
    RaporVerisi,
    VardiyaKaydi,
    VardiyaVerisi,
)
from core.rules import KuralMotoru, varsayilan_kurallar              # noqa: E402
from core import validate                                            # noqa: E402

SABLON_TALIMAT = KOK / "templates" / "taslaktalimat.xlsx"
SABLON_TNE = KOK / "templates" / "taslaktne.xlsx"
STATIK = Path(__file__).resolve().parent / "static"
AYARLAR = KOK / "ayarlar"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(KOK / "uygulama.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("beycelik")

app = FastAPI(title="Kalite Doküman Üretici", docs_url=None, redoc_url=None)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# --- Hata yönetimi -----------------------------------------------------------


@app.exception_handler(UygulamaHatasi)
async def uygulama_hatasi(_: Request, exc: UygulamaHatasi) -> JSONResponse:
    log.warning("Kullanıcı hatası: %s | %s", exc.mesaj, exc.detay or "")
    return JSONResponse(
        status_code=400, content={"hata": exc.mesaj, "detay": exc.detay}
    )


@app.exception_handler(Exception)
async def beklenmeyen_hata(_: Request, exc: Exception) -> JSONResponse:
    # Teknik iz yalnızca log dosyasına gider, kullanıcıya ASLA gösterilmez.
    log.exception("Beklenmeyen hata", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "hata": "Beklenmeyen bir sorun oluştu ve dosya üretilemedi. "
            "Girdilerinizi kontrol edip tekrar deneyin. "
            "Sorun sürerse uygulama klasöründeki uygulama.log dosyasını iletin."
        },
    )


# --- Yardımcılar -------------------------------------------------------------


def _b64_coz(deger: Any) -> bytes | None:
    """Tarayıcıdan gelen data URL veya ham base64'ü bayta çevirir."""
    if not deger or not isinstance(deger, str):
        return None
    if deger.startswith("data:"):
        _, _, deger = deger.partition(",")
    try:
        return base64.b64decode(deger)
    except Exception:
        return None


def _xlsx_yanit(veri: bytes, dosya_adi: str) -> Response:
    return Response(
        content=veri,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{dosya_adi}"'},
    )


def _paket_bayt(pkg) -> bytes:
    import zipfile

    tampon = BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as zf:
        for ad in pkg.names():
            zf.writestr(ad, pkg.read_bytes(ad))
    return tampon.getvalue()


def _kitap_bayt(wb) -> bytes:
    tampon = BytesIO()
    wb.save(tampon)
    return tampon.getvalue()


# --- Sayfa -------------------------------------------------------------------


# --- Oturum ------------------------------------------------------------------

#: Oturum gerektirmeyen uçlar.
#:
#: `/api/health` bilerek açıktır: arayüz motorun ayakta olup olmadığını
#: GİRİŞ EKRANINDA da göstermek zorundadır; kapalıysa kullanıcı boşuna
#: parola dener. Yanıtı yalnızca sürüm ve şablonların var olup olmadığıdır,
#: hiçbir belge verisi taşımaz.
ACIK_YOLLAR = frozenset(
    {"/api/health", "/api/oturum/giris", "/api/oturum/cikis", "/api/oturum/durum"}
)

#: Yola göre azami istek gövdesi (bayt).
#:
#: Sınır yokken kimlik istemeyen giriş ucuna 100 MB'lik bir gövde
#: gönderilebiliyor ve sunucu tamamını belleğe alıyordu. Birkaç eşzamanlı
#: istek fabrika makinesinin belleğini tüketmeye yeter.
#:
#: Sınırlar yolun İŞİNE göre verilir: kimlik bilgisi birkaç yüz bayttır,
#: personel listesi birkaç MB, belge üretimi ise logo ve dokuz adım
#: fotoğrafını base64 olarak taşıdığı için cömert bir paya ihtiyaç duyar.
GOVDE_SINIRI: tuple[tuple[str, int], ...] = (
    ("/api/oturum/", 4 * 1024),
    ("/api/vardiya/ice-aktar", 16 * 1024 * 1024),
    ("/api/ayarlar/", 256 * 1024),
)
VARSAYILAN_GOVDE_SINIRI = 96 * 1024 * 1024


def _govde_siniri(yol: str) -> int:
    for onek, sinir in GOVDE_SINIRI:
        if yol.startswith(onek):
            return sinir
    return VARSAYILAN_GOVDE_SINIRI


@app.middleware("http")
async def govde_boyutu(istek: Request, sonraki):
    """Content-Length'e bakarak aşırı büyük gövdeleri okumadan reddeder.

    Başlık yoksa (parçalı gönderim) boyut önceden bilinemez; tarayıcılar JSON
    gönderirken her zaman Content-Length yollar, uygulamanın tek istemcisi de
    kendi arayüzüdür. Ters vekil arkasına konursa asıl sınır orada da
    tanımlanmalıdır.
    """
    uzunluk = istek.headers.get("content-length")
    if uzunluk and uzunluk.isdigit():
        sinir = _govde_siniri(istek.url.path)
        if int(uzunluk) > sinir:
            log.warning(
                "Aşırı büyük istek reddedildi: %s %s (%s bayt, sınır %s)",
                istek.method, istek.url.path, uzunluk, sinir,
            )
            return JSONResponse(
                status_code=413,
                content={
                    "hata": "Gönderilen veri çok büyük.",
                    "detay": f"Bu uç için üst sınır {sinir // 1024} KB.",
                },
            )
    return await sonraki(istek)


@app.middleware("http")
async def oturum_denetimi(istek: Request, sonraki):
    yol = istek.url.path
    if not yol.startswith("/api/") or yol in ACIK_YOLLAR:
        return await sonraki(istek)

    if guvenlik.gecerli_mi(istek.cookies.get(guvenlik.CEREZ)):
        return await sonraki(istek)

    log.warning("Oturumsuz istek reddedildi: %s %s", istek.method, yol)
    return JSONResponse(
        status_code=401,
        content={"hata": "Oturum süresi doldu veya giriş yapılmadı. Tekrar giriş yapın."},
    )


@app.post("/api/oturum/giris")
async def api_giris(govde: dict) -> JSONResponse:
    kalan = guvenlik.kilitli_kalan_sn()
    if kalan:
        log.warning("Kilitli: giriş denemesi reddedildi (%s sn kaldı)", kalan)
        return JSONResponse(
            status_code=429,
            content={
                "hata": f"Çok fazla hatalı deneme. {kalan} saniye sonra tekrar deneyin."
            },
            headers={"Retry-After": str(kalan)},
        )

    kullanici = str(govde.get("kullanici", ""))
    parola = str(govde.get("parola", ""))

    if not guvenlik.dogrula(kullanici, parola):
        guvenlik.basarisiz_kaydet()
        # Sabit gecikme: betikle saniyede yüzlerce deneme yapmayı anlamsız
        # kılar, elle yanlış yazan kullanıcıyı rahatsız etmez.
        await asyncio.sleep(guvenlik.GECIKME_SN)
        log.warning("Başarısız giriş denemesi: %r", kullanici[:40])
        # Hangi alanın yanlış olduğu SÖYLENMEZ; doğru kullanıcı adını
        # doğrulamak deneme yanılmayı kolaylaştırır.
        return JSONResponse(
            status_code=401, content={"hata": "Kullanıcı adı veya parola hatalı."}
        )

    guvenlik.basarili_kaydet()
    yanit = JSONResponse({"durum": "acik"})
    yanit.set_cookie(
        guvenlik.CEREZ,
        guvenlik.jeton_uret(),
        max_age=guvenlik.OMUR_SN,
        httponly=True,   # sayfadaki JavaScript okuyamaz
        samesite="lax",
        path="/",
        # secure=True BİLEREK yok: uygulama fabrika makinesinde http üzerinden
        # çalışır ve Secure çerez http'de hiç gönderilmez, giriş imkânsız olur.
    )
    log.info("Oturum açıldı")
    return yanit


@app.post("/api/oturum/cikis")
async def api_cikis(istek: Request) -> JSONResponse:
    guvenlik.sonlandir(istek.cookies.get(guvenlik.CEREZ))
    yanit = JSONResponse({"durum": "kapali"})
    yanit.delete_cookie(guvenlik.CEREZ, path="/")
    return yanit


@app.get("/api/oturum/durum")
async def api_oturum_durumu(istek: Request) -> JSONResponse:
    acik = guvenlik.gecerli_mi(istek.cookies.get(guvenlik.CEREZ))
    return JSONResponse({"acik": acik})


@app.get("/")
async def anasayfa() -> FileResponse:
    return FileResponse(STATIK / "index.html")


# --- FONKSİYON 1: İş Talimatı ------------------------------------------------


@app.post("/api/talimat")
async def api_talimat(govde: dict) -> Response:
    veri = TalimatVerisi(
        baslik=govde.get("baslik", ""),
        baslik_buyuk_harf=bool(govde.get("baslik_buyuk_harf", False)),
        konu=govde.get("konu", ""),
        konu_otomatik_ek=bool(govde.get("konu_otomatik_ek", True)),
        parca_no=govde.get("parca_no", ""),
        parca_adi=govde.get("parca_adi", ""),
        musteri=govde.get("musteri", ""),
        hazirlama_tarihi=govde.get("hazirlama_tarihi", ""),
        hazirlayan=govde.get("hazirlayan", ""),
        son_rev_tarihi=govde.get("son_rev_tarihi", ""),
        musteri_temsilcisi=govde.get("musteri_temsilcisi", ""),
        son_rev_aciklamasi=govde.get("son_rev_aciklamasi", ""),
        onay=govde.get("onay", ""),
        isg_ekipmani=govde.get("isg_ekipmani", ""),
        sayfa_no=govde.get("sayfa_no", "1"),
        talimat_no=govde.get("talimat_no", ""),
        rev_no=govde.get("rev_no", "0"),
        tarih=govde.get("tarih", ""),
        logo=_b64_coz(govde.get("logo")),
        isg_ikonlari=list(govde.get("isg_ikonlari", [])),
        bos_blok_davranisi=govde.get("bos_blok_davranisi", "cerceveli"),
    )

    for i, ham in enumerate(govde.get("adimlar", [])[:9]):
        cycle = ham.get("cycle_sn")
        veri.adimlar[i] = KontrolAdimi(
            baslik=ham.get("baslik", ""),
            aciklama=ham.get("aciklama", ""),
            cycle_sn=int(cycle) if str(cycle or "").strip().isdigit() else None,
            gorsel=_b64_coz(ham.get("gorsel")),
        )

    pkg = talimat.uret(veri, SABLON_TALIMAT)
    validate.dogrula(
        pkg,
        SABLON_TALIMAT,
        beklenen_metinler=[
            f"CYCLE: {a.cycle_sn} SN"
            for a in veri.adimlar
            if a.dolu and a.cycle_sn is not None
        ],
        # Kullanıcının bilerek temizlettiği kutular "kayıp" sayılmamalı.
        metin_kutusu_silindi=len(talimat.temizlenecek_kutular(veri)),
        gorsel_silindi=talimat.silinen_isg_gorseli(veri),
    )
    log.info("İş Talimatı üretildi: %s", veri.konu or veri.baslik)
    return _xlsx_yanit(
        _paket_bayt(pkg), naming.dosya_adi(veri.konu or veri.baslik, "talimat", veri.tarih)
    )


# --- FONKSİYON 2: Tek Nokta Eğitimi ------------------------------------------


@app.post("/api/tne")
async def api_tne(govde: dict) -> Response:
    veri = TneVerisi(
        baslik=govde.get("baslik", ""),
        konu=govde.get("konu", ""),
        konu_otomatik_ek=bool(govde.get("konu_otomatik_ek", True)),
        mudurluk_birim=govde.get("mudurluk_birim", ""),
        kisim=govde.get("kisim", ""),
        hazirlayan=govde.get("hazirlayan", ""),
        parametre=govde.get("parametre", ""),
        olcum_araci=govde.get("olcum_araci", ""),
        parca_etkisi=govde.get("parca_etkisi", ""),
        sorumlu=govde.get("sorumlu", ""),
        egitim_suresi=govde.get("egitim_suresi", ""),
        egitim_tarihi=govde.get("egitim_tarihi", ""),
        tnd_no=govde.get("tnd_no", ""),
        egitim_veren=govde.get("egitim_veren", ""),
        sayfa_no=govde.get("sayfa_no", "1/1"),
        talimat_no=govde.get("talimat_no", ""),
        rev_no=govde.get("rev_no", "0"),
        tarih=govde.get("tarih", ""),
        egitim_icerigi=list(govde.get("egitim_icerigi", [])),
        egitim_turu=list(govde.get("egitim_turu", [])),
        logo=_b64_coz(govde.get("logo")),
        egitim_gorseli=_b64_coz(govde.get("egitim_gorseli")),
        katilimcilar=[
            TneKatilimci(k.get("ad_soyad", ""), k.get("sicil_no", ""))
            for k in govde.get("katilimcilar", [])
            if k.get("ad_soyad", "").strip()
        ],
    )

    pkg = tne.uret(veri, SABLON_TNE)
    validate.dogrula(pkg, SABLON_TNE, beklenen_metinler=tne.EGITIM_ICERIGI)
    log.info("TNE üretildi: %s", veri.konu or veri.baslik)
    return _xlsx_yanit(
        _paket_bayt(pkg), naming.dosya_adi(veri.konu or veri.baslik, "tne", veri.tarih)
    )


# --- FONKSİYON 3: Vardiya Listesi --------------------------------------------


def _kayitlar(ham: list) -> list[VardiyaKaydi]:
    return [
        VardiyaKaydi(
            ad_soyad=k.get("ad_soyad", ""),
            unvan=k.get("unvan", ""),
            calisma_yeri=k.get("calisma_yeri", ""),
            telefon=k.get("telefon", ""),
            durak=k.get("durak", ""),
        )
        for k in ham or []
        if k.get("ad_soyad", "").strip()
    ]


@app.post("/api/vardiya")
async def api_vardiya(govde: dict) -> Response:
    """A, B ve C vardiyalarını TEK sayfada yan yana içeren dosyayı üretir.

    Gövde `vardiyalar` listesi taşırsa üçü birden yazılır; taşımazsa tek
    vardiyalık eski biçim de kabul edilir (geriye dönük uyum).
    """
    tarih = govde.get("tarih", "")
    unvanlar = list(govde.get("normal_unvanlar") or ["Kalite Operatörü"])

    ham_vardiyalar = govde.get("vardiyalar")
    if ham_vardiyalar:
        vardiyalar = [
            VardiyaVerisi(
                vardiya_adi=v.get("vardiya_adi", ""),
                tarih=tarih,
                vardiya_saati=v.get("vardiya_saati", ""),
                kayitlar=_kayitlar(v.get("kayitlar")),
            )
            for v in ham_vardiyalar
        ]
    else:
        vardiyalar = [
            VardiyaVerisi(
                vardiya_adi=govde.get("vardiya_adi", "A"),
                tarih=tarih,
                vardiya_saati=govde.get("vardiya_saati", ""),
                kayitlar=_kayitlar(govde.get("kayitlar")),
            )
        ]

    veri = HaftalikVardiya(
        tarih=tarih, vardiyalar=vardiyalar, normal_unvanlar=unvanlar
    )
    motor = KuralMotoru(varsayilan_kurallar(unvanlar))

    toplam = sum(len(v.kayitlar) for v in veri.vardiyalar)
    log.info("Vardiya çizelgesi üretildi: %s, %d kayıt", hafta_adi(tarih), toplam)
    return _xlsx_yanit(
        _kitap_bayt(vardiya.uret(veri, motor)),
        naming.dosya_adi(hafta_adi(tarih), "vardiya", tarih),
    )


# --- FONKSİYON 4: Kalite Raporu ----------------------------------------------


@app.post("/api/rapor")
async def api_rapor(govde: dict) -> Response:
    veri = RaporVerisi(
        baslik=govde.get("baslik", ""),
        konu=govde.get("konu", ""),
        rapor_no=govde.get("rapor_no", ""),
        tarih=govde.get("tarih", ""),
        hazirlayan=govde.get("hazirlayan", ""),
        genel_durum=govde.get("genel_durum", "Açık"),
        ozet=govde.get("ozet", ""),
        satirlar=[
            RaporSatiri(
                tanim=s.get("tanim", ""),
                kok_neden=s.get("kok_neden", ""),
                duzeltici_faaliyet=s.get("duzeltici_faaliyet", ""),
                sorumlu=s.get("sorumlu", ""),
                hedef_tarih=s.get("hedef_tarih", ""),
                durum=s.get("durum", ""),
            )
            for s in govde.get("satirlar", [])
        ],
    )
    log.info("Kalite raporu üretildi: %s", veri.konu or veri.baslik)
    return _xlsx_yanit(
        _kitap_bayt(rapor.uret(veri)),
        naming.dosya_adi(veri.konu or veri.baslik, "rapor", veri.tarih),
    )


@app.get("/api/vardiya/saatler")
async def api_vardiya_saatleri() -> JSONResponse:
    """Arayüzün vardiya seçicisini kuracağı harf/saat eşlemesi."""
    return JSONResponse({"saatler": VARDIYA_SAATLERI})


@app.post("/api/vardiya/ice-aktar")
async def api_vardiya_ice_aktar(govde: dict) -> JSONResponse:
    """CSV/Excel yüklemesini ayrıştırıp tabloya basılacak kayıtları döndürür."""
    veri = _b64_coz(govde.get("icerik"))
    if veri is None:
        raise UygulamaHatasi("Dosya okunamadı. Lütfen tekrar yükleyin.")

    kayitlar = importers.oku(govde.get("dosya_adi", "liste.csv"), veri)
    log.info("İçe aktarma: %d kayıt", len(kayitlar))
    return JSONResponse(
        {
            "kayitlar": [
                {
                    "ad_soyad": k.ad_soyad,
                    "unvan": k.unvan,
                    "calisma_yeri": k.calisma_yeri,
                    "telefon": k.telefon,
                    "durak": k.durak,
                }
                for k in kayitlar
            ]
        }
    )


# --- Sağlık kontrolü ---------------------------------------------------------


@app.get("/api/health")
async def api_health() -> JSONResponse:
    """Motor durumu, şablon varlığı ve sürüm bilgisi.

    Arayüzün motor göstergesi bu uç noktayı yoklar; ISG ikon listesi yerine
    amaca yönelik bir yanıt döner.
    """
    sablonlar = {
        "talimat": SABLON_TALIMAT.is_file(),
        "tne": SABLON_TNE.is_file(),
    }
    return JSONResponse(
        {
            "durum": "acik",
            "surum": "1.0.0",
            "sablonlar": sablonlar,
            "tum_sablonlar_hazir": all(sablonlar.values()),
        }
    )


# --- Boş şablonlar -----------------------------------------------------------


@app.get("/api/bos/{tip}")
async def api_bos(tip: str) -> Response:
    if tip == "talimat":
        return _xlsx_yanit(
            _paket_bayt(talimat.bos_sablon(SABLON_TALIMAT)),
            naming.dosya_adi("BOS", "talimat"),
        )
    if tip == "tne":
        return _xlsx_yanit(
            _paket_bayt(tne.bos_sablon(SABLON_TNE)), naming.dosya_adi("BOS", "tne")
        )
    if tip == "vardiya":
        return _xlsx_yanit(
            _kitap_bayt(vardiya.bos_sablon()), naming.dosya_adi("BOS", "vardiya")
        )
    if tip == "rapor":
        return _xlsx_yanit(
            _kitap_bayt(rapor.bos_sablon()), naming.dosya_adi("BOS", "rapor")
        )
    raise UygulamaHatasi(f"'{tip}' tanınmayan bir doküman tipi.")


@app.get("/api/isg-ikonlari")
async def api_isg_ikonlari() -> JSONResponse:
    """Arayüzün seçim kutularını kuracağı İSG ekipman listesi."""
    return JSONResponse(
        {"ikonlar": [{"ad": a, "etiket": e} for a, e in isg_ikonlari.IKONLAR.items()]}
    )


@app.get("/api/isg-ikonlari/{ad}.png")
async def api_isg_ikon_gorseli(ad: str) -> Response:
    """Arayüzde önizleme için tek bir ikonu PNG olarak döndürür."""
    return Response(
        content=isg_ikonlari.uret_png(ad, 96),
        media_type="image/png",
        headers={"Cache-Control": "max-age=3600"},
    )


@app.get("/api/ayarlar/kurallar")
async def api_kurallar_oku() -> JSONResponse:
    yol = AYARLAR / "kurallar.json"
    motor = KuralMotoru.yukle(yol) if yol.is_file() else KuralMotoru()
    return JSONResponse(
        {
            "varsayilan": {
                "kalin": motor.varsayilan.kalin,
                "renk": motor.varsayilan.renk,
                "italik": motor.varsayilan.italik,
            },
            "kurallar": [
                {
                    "ad": k.ad,
                    "alan": k.alan,
                    "operator": k.operator,
                    "degerler": k.degerler,
                    "bicim": {
                        "kalin": k.bicim.kalin,
                        "renk": k.bicim.renk,
                        "italik": k.bicim.italik,
                    },
                    "etkin": k.etkin,
                }
                for k in motor.kurallar
            ],
        }
    )


@app.post("/api/ayarlar/kurallar")
async def api_kurallar_yaz(govde: dict) -> JSONResponse:
    from core.rules import BicimKurali, KayitBicimi

    ham_kurallar = govde.get("kurallar", [])
    if not ham_kurallar:
        raise UygulamaHatasi("En az bir biçimlendirme kuralı tanımlamalısınız.")

    kurallar: list[BicimKurali] = []
    for k in ham_kurallar:
        op = k.get("operator", "")
        if op not in ("listede", "listede_degil", "esittir", "icerir", "bos"):
            raise UygulamaHatasi(f"'{op}' geçerli bir operatör değil.")
        kurallar.append(
            BicimKurali(
                ad=str(k.get("ad", "Adsız kural")),
                alan=str(k.get("alan", "unvan")),
                operator=op,
                degerler=[str(d) for d in k.get("degerler", []) if str(d).strip()],
                bicim=KayitBicimi(**k.get("bicim", {})),
                etkin=bool(k.get("etkin", True)),
            )
        )

    varsayilan_ham = govde.get("varsayilan", {})
    motor = KuralMotoru(
        kurallar,
        KayitBicimi(
            kalin=bool(varsayilan_ham.get("kalin", False)),
            renk=str(varsayilan_ham.get("renk", "000000")),
            italik=bool(varsayilan_ham.get("italik", False)),
        ),
    )
    AYARLAR.mkdir(parents=True, exist_ok=True)
    motor.kaydet(AYARLAR / "kurallar.json")
    log.info("Biçimlendirme kuralları güncellendi: %d kural", len(kurallar))
    return JSONResponse({"kaydedildi": True, "kural_sayisi": len(kurallar)})


# --- Ayarlar: ünvan kuralları ------------------------------------------------


@app.get("/api/ayarlar/unvanlar")
async def api_unvanlar_oku() -> JSONResponse:
    yol = AYARLAR / "kurallar.json"
    motor = KuralMotoru.yukle(yol) if yol.is_file() else KuralMotoru()
    normal: list[str] = []
    for kural in motor.kurallar:
        if kural.operator == "listede_degil":
            normal = kural.degerler
            break
    return JSONResponse({"normal_unvanlar": normal or ["Kalite Operatörü"]})


@app.post("/api/ayarlar/unvanlar")
async def api_unvanlar_yaz(govde: dict) -> JSONResponse:
    unvanlar = [u.strip() for u in govde.get("normal_unvanlar", []) if u.strip()]
    if not unvanlar:
        raise UygulamaHatasi(
            "En az bir ünvan tanımlamalısınız; aksi halde tüm satırlar "
            "kırmızı ve kalın olur."
        )
    AYARLAR.mkdir(parents=True, exist_ok=True)
    yol = AYARLAR / "kurallar.json"
    motor = KuralMotoru.yukle(yol) if yol.is_file() else KuralMotoru(varsayilan_kurallar(unvanlar))

    guncellendi = False
    for kural in motor.kurallar:
        if kural.operator == "listede_degil" and kural.alan == "unvan":
            kural.degerler = unvanlar
            guncellendi = True
            break

    if not guncellendi:
        motor.kurallar = varsayilan_kurallar(unvanlar) + motor.kurallar

    motor.kaydet(yol)
    log.info("Ünvan kuralları güncellendi: %s", ", ".join(unvanlar))
    return JSONResponse({"normal_unvanlar": unvanlar})


# Statik varlıklar en sona bağlanır ki /api yolları gölgelenmesin.
app.mount("/static", StaticFiles(directory=STATIK), name="static")


def calistir(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    print(f"\n  Kalite Doküman Üretici çalışıyor:  http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    calistir()
