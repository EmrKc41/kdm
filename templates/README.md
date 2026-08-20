# Şablonlar

Bu klasör **boş gelir.** İçindeki dosyalar bir kurumun gerçek kalite
dokümanlarıdır ve depoda tutulmaz.

Uygulamayı çalıştırmadan önce kendi şablonlarınızı buraya koyun:

| Dosya | Kullanan fonksiyon |
|---|---|
| `taslaktalimat.xlsx` | İş Talimatı |
| `taslaktne.xlsx` | Tek Nokta Eğitimi |

Dosya adları **küçük harfli** olmalıdır. Vardiya Listesi ve Kalite Raporu
şablon kullanmaz; sıfırdan üretilir.

## Şablonlardan ne bekleniyor

Program bu dosyaları bir ZIP arşivi olarak açar ve yalnızca hedeflediği XML
parçalarını değiştirir; dokunulmayan her parça baytı baytına korunur. Bunun
nedeni ana `README.md` içinde anlatılıyor — kısaca: kontrol adımı etiketleri
ve onay kutuları hücre değeri değil, çizim nesnesidir ve openpyxl bunları
sessizce siler.

Bu yüzden şablonun yapısı önemlidir:

* **`taslaktalimat.xlsx`** — A3 yatay, 23×53 hücrelik talimat sayfası.
  Çizim katmanında `1. KONTROL ADIMI` … `9. KONTROL ADIMI` metin kutuları,
  bir adet `CYCLE:` kutusu, `Resim 1` adlı logo görseli ve V7:W7 alanında
  İSG piktogramları (`Picture 39/40/41`) bulunur.
* **`taslaktne.xlsx`** — Tek nokta eğitimi formu. Eğitim içeriği ve türü
  onay kutuları, hücre dolgusu değil küçük çizim dikdörtgenleridir.

Şablonu Excel'de açıp kaydetmeyin: Excel çizim nesnelerini yeniden yazar ve
çıktı doğrulayıcı bunu fark ederek üretimi durdurur.

## Şablon yoksa ne olur

Uygulama açılır ve durum rozeti şablonların eksik olduğunu bildirir; Vardiya
Listesi ile Kalite Raporu çalışmaya devam eder. Test takımında şablona bağlı
testler düşmez, **atlanır** (`tests/conftest.py`).
