# Kalite Doküman Merkezi

Otomotiv yan sanayi kalite dokümanlarını formdan doldurarak, kurum
şablonlarıyla piksel düzeyinde uyumlu ve baskıya hazır `.xlsx` dosyaları
olarak üretir.

| Fonksiyon | Referans şablon | Çıktı |
|---|---|---|
| **İş Talimatı** | `taslaktalimat.xlsx` | 9 kontrol adımlı, 23×53 hücrelik A3 yatay talimat |
| **Tek Nokta Eğitimi** | `taslaktne.xlsx` | Onay kutulu, katılımcı imza listeli TNE formu |
| **Vardiya Listesi** | — (sıfırdan tasarım) | Filtreli, dondurulmuş başlıklı A4 yatay personel listesi |
| **Kalite Raporu** | — (sıfırdan tasarım) | Uygunsuzluk takip tablosu, A4 dikey düzeltici faaliyet raporu |

---

## Neden openpyxl ile yazmıyoruz?

Bu projedeki en kritik teknik karar budur.

`taslaktalimat.xlsx` içindeki **"1. KONTROL ADIMI" … "9. KONTROL ADIMI"** ve
**"CYCLE: 3 SN"** etiketleri hücre değeri değildir; `xl/drawings/drawing1.xml`
içinde yaşayan çizim nesneleridir (text box). Aynı şekilde TNE'deki **eğitim
içeriği / eğitim türü onay kutuları** da hücre dolgusu değil, küçük çizim
dikdörtgenleridir.

openpyxl bir dosyayı açıp kaydettiğinde bu nesneleri **sessizce siler.**
Ölçülen sonuç:

| | Orijinal şablon | `load_workbook()` → `save()` sonrası |
|---|---|---|
| Çizim anchor sayısı | 15 | **5** |
| Metin kutusu (`<xdr:sp>`) | **10** | **0 — hepsi silindi** |
| ZIP parça sayısı | 30 | 18 |

Ayrıca `xl/printerSettings1.bin` (kağıt/yazıcı ayarı), `customXml/item1-3`
(doküman metadatası), `docMetadata/LabelInfo.xml` ve `sharedStrings.xml` de
kaybolur.

**Bu yüzden Fonksiyon 1 ve 2, xlsx dosyasını bir ZIP arşivi olarak açar ve
yalnızca hedeflenen XML parçalarını düzenler.** Dokunulmayan her parça baytı
baytına korunur. Vardiya listesinde (Fonksiyon 3) şablon ve çizim nesnesi
olmadığı için openpyxl ile yazmak güvenlidir ve orada kullanılır.

Bu davranış `tests/test_talimat.py::test_openpyxl_referans_testi_basarisiz_olur`
testiyle sürekli doğrulanır: openpyxl çıktısı doğrulayıcıyı **düşürmelidir.**
Düşmezse doğrulayıcı sahte güven veriyor demektir.

---

## Kurulum

Python 3.11+ ve Node.js 20+ gerekir. Excel'in kurulu olması **gerekmez.**

```bash
pip install -r requirements.txt
```

```bash
cd web && npm install
```

İnternet erişimi olmayan bir fabrika makinesi için, erişimi olan bir bilgisayarda:

```bash
pip download -r requirements.txt -d paketler
```

`paketler` klasörünü hedef makineye kopyalayıp:

```bash
pip install --no-index --find-links=paketler -r requirements.txt
```

### Şablonlar

`templates/` klasörü **bu depoda boş gelir.** İçine konması gereken
dosyalar bir kurumun gerçek kalite dokümanlarıdır ve depoda tutulmaz.
Kendi şablonlarınızı buraya koyun:

| Dosya | Kullanan fonksiyon |
|---|---|
| `taslaktalimat.xlsx` | İş Talimatı |
| `taslaktne.xlsx` | Tek Nokta Eğitimi |

Dosya adları küçük harfli olmalıdır. Şablonlardan tam olarak ne beklendiği
`templates/README.md` içinde anlatılıyor.

Bu dosyalar **salt okunur** kabul edilir; program hiçbir koşulda üzerlerine
yazmaz, her zaman kopya üzerinde çalışır.

Şablon yoksa uygulama yine açılır: Vardiya Listesi ve Kalite Raporu
şablon kullanmaz, çalışmaya devam eder. Test takımında şablona bağlı
testler düşmez, **atlanır** — şablonsuz bir klonda `pytest` 89 geçer /
87 atlar, Playwright 30 geçer / 5 atlar; hiçbiri kırmızı olmaz.

---

## Çalıştırma

### En kolay yol (Windows)

Terminalle uğraşmak istemiyorsanız iki dosya yeter:

| Dosya | Ne yapar |
|---|---|
| `kur.bat` | **Bir kez** çalıştırılır. Python ortamını kurar, paketleri indirir, arayüzü derler. |
| `baslat.bat` | Her açılışta çift tıklanır. Programı başlatır ve tarayıcıyı açar. |

`kur.bat` yalnızca Python 3.11+ ve Node.js 20+ ister; ikisi de yoksa nereden
kurulacağını söyler ve durur. Paketleri projeye ait bir `.venv` klasörüne
kurar, bilgisayarın geneline bulaştırmaz.

### Terminalden

Uygulama iki parçadan oluşur: **Excel motoru** (Python/FastAPI) ve **web
arayüzü** (Next.js). İkisini birden başlatmak için:

```bash
python calistir.py
```

Sonra tarayıcıdan **http://localhost:3000** adresini açın.

Ayrı ayrı başlatmak isterseniz:

```bash
python -m uvicorn ui.app:app --host 127.0.0.1 --port 8000
```

```bash
cd web && npm run dev
```

Arayüz `/api/*` isteklerini Next.js üzerinden motora yönlendirir
(`web/next.config.ts`), böylece tarayıcı tek origin görür ve CORS ayarı
gerekmez. Motorun adresi `MOTOR_ADRESI` ortam değişkeniyle değiştirilebilir.

### Giriş

Uygulama bir giriş ekranının arkasındadır. Varsayılan kimlik bilgileri
**admin / admin**'dir.

> **Kullanmaya başlamadan önce parolayı değiştirin.** Varsayılan kimlik
> bilgileri bu deponun kaynak kodunda açıkça yazılıdır; değiştirilmediği
> sürece hiçbir koruma sağlamazlar. Aşağıdaki ortam değişkenleriyle
> değiştirilir.

Doğrulama **motorda** yapılır (`ui/guvenlik.py`): `/api/*` uçlarının tamamı
geçerli bir oturum çerezi ister, aksi halde **401** döner. Arayüzü atlayıp
`:8000` adresine doğrudan istek göndermek de reddedilir.

```
POST /api/oturum/giris    {kullanici, parola}  → oturum çerezi kurar
POST /api/oturum/cikis                          → oturumu sonlandırır
GET  /api/oturum/durum                          → {acik: true|false}
```

Kimlik bilgileri ortam değişkenleriyle değiştirilir:

```bash
set KDU_KULLANICI=kalite
set KDU_PAROLA=uzun-bir-parola
python calistir.py
```

**Tasarım notları:**

* Jeton **HttpOnly** çerezde taşınır; sayfadaki JavaScript okuyamaz. Başlık
  (`Authorization`) kullanılmadı çünkü İSG ikonları `<img src="/api/...">`
  ile yükleniyor ve tarayıcı `<img>` isteklerine başlık eklemez — çerez ise
  kendiliğinden gider ve tek mekanizma her iki durumu da kapsar.
* `Secure` bayrağı **bilerek yok**: uygulama fabrika makinesinde `http`
  üzerinden çalışır ve `Secure` çerez `http`'de hiç gönderilmez.
* `/api/health` oturumsuz erişilebilir; giriş ekranı motorun ayakta olup
  olmadığını göstermek zorundadır. Yanıtı yalnızca sürüm ve şablonların
  var olup olmadığıdır, hiçbir belge verisi taşımaz.
* Oturumlar **bellekte** tutulur ve 12 saat (bir vardiya) yaşar. Motor
  yeniden başlarsa oturumlar düşer; kalıcı depo bilerek eklenmemiştir.

> **Sınır:** Tek bir paylaşılan hesap vardır ve parola düz metin olarak
> karşılaştırılır (`hmac.compare_digest` ile, zamanlama sızıntısına karşı).
> Bu, tek makinede çalışan bir fabrika aracı için yeterlidir; birden çok
> kullanıcı, parola özeti ve rol ayrımı gerekirse ayrıca kurulmalıdır.

---

## Kötüye kullanıma karşı korumalar

Aşağıdaki sınırların her biri **ölçülmüş** bir açığı kapatır; sayılar
tahmin değil, düzeltme öncesi gözlenen davranıştan gelir. Hepsi
`tests/test_guvenlik.py` ile korunur.

| Koruma | Nerede | Ölçülen açık |
|---|---|---|
| Giriş yavaşlatma ve kilit | `ui/guvenlik.py` | 30 yanlış parola **0,2 saniyede** deneniyordu; sınır yoktu |
| İstek gövdesi sınırı | `ui/app.py` | Kimlik istemeyen giriş ucu **100 MB**'lık gövdeyi tamamen belleğe alıyordu |
| Sıkıştırma bombası denetimi | `core/importers.py` | **455 KB**'lik bir xlsx, bellekte **101 MB**'a açılıp ayrıştırılıyordu |
| Görsel piksel sınırı | `core/imaging.py` | **0,43 MB**'lik 144 megapiksel PNG kabul edilip ~430 MB ayırıyordu |
| Güvenlik başlıkları | `web/next.config.ts` | Uygulama çerçevelenebiliyordu (clickjacking) |

**Giriş yavaşlatma:** 8 ardışık hatalı denemeden sonra 30 saniye kilit,
her hatalı denemede 0,3 saniye gecikme. Sayaç **küreseldir**, istemci
adresine göre değil — istekler Next.js yönlendiricisi üzerinden geldiği
için motora hepsi `127.0.0.1`'den ulaşır ve adrese göre ayırmak yanıltıcı
bir güven verirdi. Bedeli, saldırganın gerçek kullanıcıyı da kısa süre
kilitleyebilmesidir; bu yüzden kilit bilerek kısa tutulmuştur.

**Gövde sınırları** yolun işine göre verilir: oturum uçları 4 KB, personel
listesi içe aktarma 16 MB, belge üretimi 96 MB (logo ve dokuz adım
fotoğrafını base64 olarak taşır).

**CSRF:** Oturum çerezi `SameSite=Lax` taşır; tarayıcı başka bir sitenin
tetiklediği POST isteğine bu çerezi eklemez. Ayrı bir CSRF jetonu bu
nedenle gerekmez.

**CSP** üretimde dardır. Geliştirmede React `eval()`, Next ise sıcak
yeniden yükleme için WebSocket ister; bu izinler yalnızca
`NODE_ENV=development` iken verilir ve bir e2e testi üretime sızmadıklarını
doğrular.

### Neden iki parça?

Excel motoru şablonları ZIP/XML seviyesinde işler — metin kutuları, yazıcı
ayarları ve doküman metadatası ancak böyle korunuyor (bkz. yukarıdaki bölüm).
Bu katmanın JavaScript karşılığı yok. Arayüz ise tamamen Next.js; Python
yalnızca arka planda belge üretir ve hiçbir HTML sunmaz.

### İnternetsiz çalışma

Fontlar `next/font` ile **derleme sırasında** indirilip kendi sunucumuzdan
servis edilir; çalışma anında Google Fonts'a istek gitmez. İkonlar
(`lucide-react`) paket içinde gelir. Fabrika makinesinde:

```bash
cd web && npm ci --omit=dev && npm run build
```

komutları internet erişimi olan bir makinede çalıştırılıp `web/` klasörü
kopyalanabilir; ardından `python calistir.py --uretim` ile açılır.

---

## Kullanım

### İş Talimatı

1. **Talimat adı** zorunludur; A1:U4 alanına Calibri 24 punto, kalın, ortalı yazılır.
   Başlık varsayılan olarak yazdığınız gibi aktarılır. "Büyük harfe çevir"
   kutusunu işaretlerseniz Türkçe kurallarına göre büyütülür
   (`i → İ`, `ı → I`).
2. **Konu** alanına parça referansını yazın (örn. `10598-AG`). Program sonuna
   otomatik olarak `İŞ TALİMATI HK.` ekler; istemezseniz kutuyu kaldırın.
   Alanın altındaki önizleme çıktıyı canlı gösterir.
3. **Logo** yükleyin. Çıktıda tam **1,55 × 3,28 cm** (558000 × 1180800 EMU)
   ölçüsüne getirilir; en-boy oranı korunur, taşan kenarlar kırpılır.
   F6:G7 alanındaki **SC (özel karakteristik) sembolü şablonda sabittir** ve
   hiç değiştirilmez — kullanıcıdan istenmez.
4. **İSG ekipmanı** ikonlarını seçin. Şablonun küçük ve okunaksız
   piktogramları yerine ISO 7010 biçiminde (mavi daire, beyaz sembol)
   ikonlar üretilir: baret, koruyucu gözlük, kulaklık, eldiven, emniyet
   ayakkabısı, toz maskesi, reflektif yelek, yüz siperliği. Seçilenler
   V7:W7 alanına eşit ölçüde ve ortalanmış olarak dizilir; alana 5 ikon
   rahatça sığar. Hiç seçim yapılmazsa şablonun mevcut piktogramlarına
   dokunulmaz.
5. **Tarih alanları** takvimden seçilir ve `GG.AA.YYYY` biçiminde yazılır.
6. **Kontrol adımları:** 9 kart hazır gelir. İstediğiniz kadarını doldurun.
   * Her adıma fotoğraf yükleyin — çıktıda tam **5 × 17 cm**, yatay ortalı,
     üstten hizalı ve **metin kutularının arkasında** yer alır.
   * Cycle süresini saniye olarak girin; `CYCLE: <değer> SN` biçiminde yazılır.
     Şablonda tek cycle kutusu vardır; kalan 8 tanesi aynı kenarlık, dolgu ve
     puntoyla klonlanır.
   * Sarı alan başlığı **kırmızı**, açıklama **siyah** olarak aynı hücreye
     alt alta yazılır; **ikisi de kalındır.** Kartın altındaki önizleme
     sonucu gösterir.
   * Kartın üst şeridinden tutup sürükleyerek **adım sırasını değiştirebilirsiniz.**
   * Doldurulmayan bloklar için iki seçenek: *boş ama çerçeveli bırak* veya
     *başlık ve cycle kutularını temizle.*
7. **Excel Dosyası Üret** düğmesine basın.

### Tek Nokta Eğitimi

* Başlık şablonda 36 punto olmasına rağmen, talep gereği **24 punto** uygulanır.
* **Eğitim içeriği** ve **eğitim türü** kutularından seçtikleriniz çıktıda
  yeşil (`00B050`) dolgu alır. Şablonda hazır işaretli gelen kutular (KALİTE,
  TEMEL BİLGİ, HATA) seçilmediyse **temizlenir.**

  > **Dolgu ile kenarlık ayrımı.** Bir onay kutusunun `<xdr:spPr>` bloğunda
  > önce DOLGU, sonra `<a:ln>` (KENARLIK) gelir ve ikisinin de kendi
  > `<a:solidFill>` tanımı vardır. Şablondaki İYİLEŞTİRME kutusunun dolgusu
  > tema rengiyle (`schemeClr bg1`), kenarlığı ise `srgbClr 000000` ile
  > tanımlıdır. Tüm `spPr` üzerinde arama yapan bir uygulama kenarlık rengini
  > dolgu sanır ve kutuyu doldurmak yerine **çerçevesini** boyar. Bu yüzden
  > `set_fill` yalnızca `<a:ln>` öncesindeki bölgeye dokunur; dört regresyon
  > testi kenarlıkların şablonla birebir aynı kaldığını doğrular.
* **Eğitim görseli** B11:G42 alanını en-boy oranı korunarak tamamen doldurur ve
  arkaya gönderilir.
* **Katılımcılar** en fazla 32 kişidir (satır 11–42). İmza sütunu ıslak imza
  için bilinçli olarak boş bırakılır.
* TNE logosu **şablondaki ölçüsünü korur** (6,76 × 3,43 cm) — İş Talimatı'ndaki
  1,55 × 3,28 cm ölçüsünden farklıdır ve bilinçli olarak öyle bırakılmıştır.

### Vardiya Listesi

* Satırları elle ekleyebilir veya **CSV / Excel içe aktarabilirsiniz.**
  Sütun başlıkları esnek eşleşir: `Ad Soyad`, `isim`, `personel` gibi
  varyantlar tanınır. Türkçe kodlamalar (UTF-8, CP1254, ISO-8859-9)
  otomatik denenir.
* **Biçimlendirme kuralı:** Ünvanı ayarlardaki normal listede **olmayan** her
  kayıt kırmızı ve kalın yazılır. Tabloda da aynı şekilde gösterilir, böylece
  çıktıyı üretmeden önce görürsünüz.
* Telefon numaraları metin biçiminde (`@`) yazılır — **baştaki sıfır kaybolmaz.**
* Çıktı: dondurulmuş başlık satırı, otomatik filtre, kurumsal renkli başlık
  bandı, alternatif satır gölgelendirmesi, ince kenarlıklar, otomatik sütun
  genişliği, A4 yatay, her sayfada tekrarlayan başlık satırı, sayfa numaralı
  alt bilgi ve vardiya bilgisini taşıyan üst bilgi.

### Ünvan kurallarını değiştirme

**Ayarlar** sekmesinden normal (siyah) yazılacak ünvan listesini
genişletebilirsiniz. Kural motoru sabit kodlanmamıştır; kurallar
`ayarlar/kurallar.json` dosyasında veri olarak saklanır ve şu operatörleri
destekler: `listede`, `listede_degil`, `esittir`, `icerir`, `bos`.

### Proje dosyası

Her formun alt çubuğunda **Projeyi Kaydet** ve **Proje Yükle** düğmeleri
vardır. Girdiğiniz her şey — görseller data URL olarak dahil — şablonlardan
bağımsız bir `.json` dosyasına yazılır, yarım kalan işinize sonra dönersiniz.

Dosya biçimi Python tarafıyla (`core/models.py`) aynıdır:

```json
{ "surum": 1, "tip": "talimat", "veri": { ... } }
```

Vardiya projesi **üç vardiyayı birden** taşır; yalnızca ekranda açık olanı
değil. Ünvan kural listesi de dosyaya yazılır, böylece proje başka bir
makinede açıldığında renklendirme aynı kalır.

Yükleme sırasında üç denetim yapılır ve hiçbiri sessizce yutulmaz:

| Durum | Mesaj |
|---|---|
| Sürüm uyuşmazlığı | "Proje dosyası bu sürümle uyumlu değil. Beklenen sürüm 1, dosyadaki 99." |
| Yanlış sekme | "Bu dosya bir \"İş Talimatı\" projesi. Vardiya Listesi sekmesine yüklenemez." |
| Bozuk JSON | "\"bozuk.json\" geçerli bir proje dosyası değil veya bozulmuş." |

---

## Üretilen dosya adları

```
<KONU>_<DOKUMAN_TIPI>_<TARIH>.xlsx
```

Örnek: `10598_AG_IS_TALIMATI_17.08.2026.xlsx`

Dosya **içeriğinde** Türkçe karakterler UTF-8 olarak korunur; dosya **adında**
güvenli ASCII karşılıklarına çevrilir (`ç→c`, `ğ→g`, `ı→i`, `İ→I`, `ö→o`,
`ş→s`, `ü→u`), böylece dosya farklı sistemler ve ağ paylaşımları arasında
sorunsuz taşınır.

---

## Arayüz tasarımı

Tasarım kararları tahmine değil, `ui-ux-pro-max` skill'inin veritabanına
dayanır; üretilen sistem `design-system/kalite-dokuman-uretici/MASTER.md`
dosyasında saklıdır.

| Karar | Değer |
|---|---|
| Stil | **Data-Dense Dashboard** — yoğun veri girişi, minimal boşluk |
| Ana renk | `#1E40AF` (açık tema) · `#60A5FA` (koyu tema) |
| Vurgu | `#D97706` amber — birincil eylem düğmesi |
| Tipografi | **Fira Sans** (gövde) · **Fira Code** (veri, kod, sayı) |
| Tema | Açık + koyu; koyu tema ters çevirme değil, ayrı tonal palet |

Uygulanan erişilebilirlik önlemleri ve ölçülen değerler:

| Denetim | Sonuç |
|---|---|
| Gövde metni kontrastı | açık **9,9:1** · koyu **15,2:1** (AAA) |
| İkincil metin kontrastı | **7,2:1** (AAA) |
| 375px'te yatay taşma | **0 px** |
| Dokunmatik hedefler (`pointer: coarse`) | **44 px** — masaüstünde yoğunluk korunur |
| `prefers-reduced-motion` | tüm animasyonlar durdurulur |
| Klavye ile adım sıralama | dnd-kit `KeyboardSensor` ile destekli |
| İkonlar | SVG (`lucide-react`) — emoji kullanılmaz |

**Excel alanlarının önizlemeleri gerçek renklerle çizilir.** Sarı açıklama
alanı `#FFFF00` zemin, kırmızı kalın başlık ve siyah kalın açıklama olarak
kartın altında canlı gösterilir; TNE onay kutuları `#00B050` yeşiliyle
işaretlenir. Bu renkler tema değişkeni değildir — karanlık modda da kağıttaki
görüntü aynı kalmalıdır.

---

## Şablona yapılan bilinçli müdahaleler

Kural şudur: şablona dokunulmaz. Aşağıdakiler bu kuralın açıkça kararlaştırılmış
tek istisnalarıdır ve testlerle sabitlenmiştir.

| Ne | Şablonda | Çıktıda | Neden |
|---|---|---|---|
| Konu puntosu (C5) | 22 | **14** | Talep |
| Parça no / adı puntosu (C6, C7) | 14 | **10** | Talep |
| Sarı alan puntosu | 12 / 16 | **14** | Talep |
| Sarı alandaki siyah açıklama | — | **kalın** | Talep |
| TNE başlık puntosu (B2) | 36 | **24** | Talep |
| **P sütunu genişliği** | 27,7109375 | **26,57** | Baskıda milimetrik kayma |
| İSG piktogramları (V7:W7) | 3 adet küçük görsel | Seçilen ISO 7010 ikonları | Okunaksızdı |

Bunların dışında hiçbir sütun genişliği, satır yüksekliği, birleşik hücre,
kenarlık veya baskı ayarı değişmez; çıktı doğrulayıcı her üretimde bunu
denetler.

---

## Çıktı doğrulayıcı

Her dosya diske yazılmadan **önce** `core/validate.py` çalışır. Denetlenenler:

* Şablondaki hiçbir ZIP parçası kaybolmamış mı (özellikle `printerSettings`,
  `customXml`, `docMetadata`)
* `pageSetup`, `pageMargins`, `printOptions`, `cols` baytı baytına aynı mı
* Birleşik hücre listesi birebir aynı mı
* Metin kutusu sayısı korunmuş mu (kullanıcının bilerek temizlettikleri hariç)
* Görsel sayısı korunmuş mu (İSG alanında bilinçli çıkarılanlar hariç)
* Beklenen metin kutusu yazıları çıktıda var mı
* Görsel ölçüleri **EMU cinsinden tam** eşit mi
* Kontrol adımı görselleri metin kutularının **arkasında** mı (z-sırası)
* Üretilen tüm XML parçaları hâlâ ayrıştırılabilir mi

Bir bulgu varsa `DogrulamaHatasi` fırlatılır ve **dosya yazılmaz.** Program
hiçbir koşulda sessizce bozuk dosya üretmez.

---

## Testler

```bash
python -m pytest tests/ -q
```

176 test; şablon sadakati, EMU ölçüleri, z-sırası, onay kutusu eşleştirmesi,
Türkçe karakter korunumu, kural motoru, CSV içe aktarma, görsel boyut
koruması, oturum doğrulaması, kötüye kullanım sınırları ve API
uçları kapsanır. Testler ek bağımlılık gerektirmez.

```bash
cd web && npx playwright test
```

35 arayüz testi; dört fonksiyonun form doldurma → xlsx indirme akışı, dosya
adı kuralları, proje kaydet/yükle turu, klavye kısayolları, erişilebilirlik
davranışları ve giriş ekranı kapsanır.

Playwright **iki sunucuyu birden** ayağa kaldırır (uvicorn + Next.js), yani
üretim akışları gerçek motora karşı koşar. Yalnızca Next.js başlatmak, xlsx
üreten akışları sessizce test dışı bırakır. Next 16 aynı dizinden ikinci bir
dev sunucusuna izin vermediği için, testlerden önce çalışan `next dev`
varsa durdurulmalıdır.

CI: her push/PR'da GitHub Actions `pytest` + `npm run lint` + `npm run build`
+ `npm run test:e2e` (Playwright) çalıştırır (`.github/workflows/ci.yml`).

---

## Legacy arayüz notu

`:8000` adresindeki FastAPI kök yolu artık yalnızca Next.js arayüzüne
yönlendiren ince bir bilgi sayfasıdır. Eski `ui/static/app.js` kaldırıldı;
birincil arayüz her zaman **http://localhost:3000** üzerindedir.

---

## Proje yapısı

```
core/                       Şablon doldurma mantığı — arayüzden tamamen bağımsız
  units.py                  EMU / piksel / cm dönüşümleri ve zorunlu ölçü sabitleri
  models.py                 Form verisi + JSON proje dosyası
  imaging.py                En-boy oranı koruyarak kutuya sığdırma (Pillow)
  isg_ikonlari.py           ISO 7010 biçiminde İSG ekipman ikonlarının çizimi
  rules.py                  Biçimlendirme kural motoru (veri odaklı)
  importers.py              CSV / Excel içe aktarma
  validate.py               Çıktı doğrulayıcı
  naming.py                 Dosya adı üretimi
  textutil.py               Türkçe'ye duyarlı büyük/küçük harf
  errors.py                 Kullanıcıya gösterilebilir hata tipleri
  ooxml/
    package.py              xlsx'i ZIP olarak aç / parça değiştir / yaz
    sheet.py                Hücre değeri yazma (inlineStr, zengin metin)
    styles.py               Punto/renk türetme (mevcut stiller korunur)
    drawing.py              Metin kutusu ve görsel cerrahisi, z-sırası
    layout.py               Sütun genişliği / satır yüksekliği geometrisi
  generators/
    talimat.py              Fonksiyon 1
    tne.py                  Fonksiyon 2
    vardiya.py              Fonksiyon 3
    rapor.py                Fonksiyon 4
ui/
  app.py                    FastAPI uçları (yalnızca JSON + xlsx döndürür)
web/                        Next.js 16 · TypeScript · Tailwind v4 · shadcn/ui
  app/globals.css           Tasarım sistemi tokenları (açık + koyu tema)
  components/talimat/       Kontrol adımı kartları, sürükle-bırak, İSG seçici
  components/tne/           Tek nokta eğitimi formu
  components/vardiya/       Vardiya anahtarı ve personel tablosu
  components/ortak/         Görsel yükleme, bölüm/alan sarmalayıcıları
  lib/                      API istemcisi, tipler, tarih ve dosya yardımcıları
design-system/              ui-ux-pro-max ile üretilen tasarım sistemi
templates/                  Şablonlar — SALT OKUNUR
tests/                      pytest
ayarlar/kurallar.json       Ünvan biçimlendirme kuralları (çalışırken oluşur)
uygulama.log                Teknik günlük
```

Yeni bir form tipi eklemek için `core/generators/` altına bir modül yazıp
`ui/app.py` içine bir uç eklemek yeterlidir; arayüz ve çekirdek ayrıktır.

---

## Sık karşılaşılan sorunlar

**"Şablon dosyası bulunamadı"**
`templates/` klasöründe `taslaktalimat.xlsx` ve `taslaktne.xlsx` olduğundan
emin olun. Dosya adları küçük harfli olmalıdır.

**"Üretilen dosya şablon sadakat denetimini geçemedi"**
Şablon dosyası değişmiş olabilir (örneğin Excel'de açılıp kaydedilmiş).
Şablonun orijinal kopyasını geri koyun. Hata mesajının altındaki detay,
tam olarak neyin kaybolduğunu söyler.

**Sarı alan metni sığmıyor uyarısı**
Başlık + açıklama toplamı 250 karakteri aşıyor. Program metni **sessizce
kırpmaz**; kısaltmanız gerekir. Kart altındaki sayaç anlık uzunluğu gösterir.

**İçe aktarmada "Ad Soyad sütunu bulunamadı"**
CSV'nin ilk satırı başlık satırı olmalıdır. Ayraç olarak `;` `,` sekme veya
`|` kullanılabilir; program otomatik saptar.

**Telefon numarasının başındaki sıfır kayıp**
Kaynak Excel dosyasında numara *sayı* olarak saklanmışsa sıfır zaten
kaybolmuştur. Program uydurma veri üretmez. Kaynak dosyada sütunu metin
biçimine çevirip tekrar aktarın.

**Excel dosyayı onarmak istiyor**
Bu olmamalıdır. Olursa `uygulama.log` dosyasını ve kullandığınız girdileri
iletin — çıktı doğrulayıcının kaçırdığı bir durum var demektir.

---

## Masaüstü paketi (isteğe bağlı)

```bash
pip install pyinstaller
pyinstaller --onefile --name KaliteDokumanMerkezi ^
  --add-data "ui/static;ui/static" ^
  --add-data "templates;templates" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.protocols.http.h11_impl ^
  ui/app.py
```

Üretilen `dist/KaliteDokumanMerkezi.exe` çift tıklanarak çalıştırılır.

> **Not:** Masaüstü paketi yalnızca Excel motorunu başlatır. Tam arayüz için
> `python calistir.py --uretim` kullanın veya Next.js build'ini ayrıca
> dağıtın. PyInstaller entegrasyonu güncellenmeyi bekliyor (yol haritası P0).
