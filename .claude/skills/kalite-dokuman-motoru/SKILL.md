---
name: kalite-dokuman-motoru
description: >
  Kalite Doküman Üretici projesinde (talimatdeneme) Excel şablonlarına
  dokunan her iş için zorunlu kurallar: openpyxl yasağı ve ZIP/XML cerrahisi,
  çizim nesnesi (metin kutusu) koruma, dolgu/kenarlık ayrımı, Türkçe büyük
  harf, uvicorn --reload zorunluluğu, SSR'de deterministik kimlik, iki
  sunuculu Playwright kurulumu. Bu depoda core/, ui/, templates/ veya
  web/ altında ÇALIŞMAYA BAŞLAMADAN ÖNCE bu skill'i aç — kullanıcı şablon,
  xlsx, talimat, TNE, vardiya, rapor, İSG ikonu, hücre biçimi, çizim
  nesnesi, dosya adı ya da arayüz formu konularından herhangi birini
  ima etse bile geçerlidir. Buradaki kuralların her biri üretimde kırılmış
  ve kullanıcıya bozuk dosya gitmesine yol açmış gerçek hatalardan gelir.
---

# Kalite Doküman Üretici — motor kuralları

Bu proje otomotiv yan sanayi için baskıya hazır `.xlsx` üretir. Çıktı
şablonla **piksel düzeyinde** uyumlu olmak zorundadır: dosyalar fabrikada
yazdırılır ve müşteri denetiminde delil sayılır. Aşağıdaki kuralların hepsi
tek tek kırıldı ve her biri kullanıcıya bozuk dosya gönderilmesine yol açtı.

## 1. openpyxl ile şablon açıp kaydetme

`taslaktalimat.xlsx` ve `taslaktne.xlsx` içindeki "1. KONTROL ADIMI",
"CYCLE: 3 SN" etiketleri ve TNE onay kutuları **hücre değeri değildir**;
`xl/drawings/drawing1.xml` içinde yaşayan çizim nesneleridir.

`load_workbook()` → `save()` bunları **sessizce siler**: çizim anchor 15→5,
metin kutusu 10→0, ZIP parçası 30→18. `printerSettings1.bin`, `customXml/`
ve `sharedStrings.xml` de kaybolur. Hata vermez — bu yüzden tehlikelidir.

- **Fonksiyon 1 (talimat) ve 2 (TNE):** xlsx'i ZIP olarak aç, yalnızca
  hedeflenen XML parçalarını değiştir (`core/ooxml/package.py`).
  Dokunulmayan her parça baytı baytına korunur.
- **Fonksiyon 3 (vardiya) ve 4 (rapor):** şablon yok, sıfırdan üretiliyor;
  orada openpyxl güvenlidir ve bilerek kullanılır.

`tests/test_talimat.py::test_openpyxl_referans_testi_basarisiz_olur` bunu
sürekli doğrular: openpyxl çıktısı doğrulayıcıyı **düşürmelidir**. Düşmezse
doğrulayıcı sahte güven veriyordur — testi "düzeltme", doğrulayıcıyı onar.

## 2. Dolgu ile kenarlığı karıştırma

`<xdr:spPr>` içinde önce dolgu, sonra `<a:ln>` gelir ve **ikisinin de**
`<a:solidFill>` çocuğu vardır. Tüm `spPr` içinde ilk `solidFill`'i aramak,
kutuyu doldurmak yerine çerçevesini boyar. Önce `<a:ln>` sınırını bul,
dolguyu yalnızca ondan önceki bölgede ara (`core/ooxml/drawing.py`).

## 3. Python'un `.upper()` Türkçe'de bozuk

`"ısı".upper()` → `"ISI"` yerine yanlış sonuç verir; `i` → `I` olur, `İ`
olmaz. Kullanıcıya giden her büyük harf dönüşümü `core/textutil.py`
üzerinden geçmeli. Arayüz tarafında da aynısı geçerlidir
(`toLocaleUpperCase("tr")`).

Dosya **adlarında** ise tam tersi istenir: Türkçe karakterler ASCII'ye
indirgenir (`core/naming.py`), çünkü dosyalar ağ paylaşımları ve farklı
işletim sistemleri arasında taşınır. İçerik UTF-8 kalır.

## 4. Geliştirmede uvicorn'u `--reload` olmadan başlatma

uvicorn kodu bir kez yükler. `core/` altında düzeltme yapıp sunucuyu
yeniden başlatmazsan arayüz **eski çıktıyı** üretmeye devam eder. Bu bir
kez yaşandı: düzeldiği sanılan hata kullanıcıya gitti.

```bash
python -m uvicorn ui.app:app --reload --reload-dir core --reload-dir ui --port 8000
```

`calistir.py` bunu zaten yapar; elle başlatırken atlamak kolaydır.

Bu tuzağın ikinci ve daha sinsi yüzü: uvicorn'un yeniden yükleyici süreci
öldürüldüğünde **işçi süreci hayatta kalıp 8000 portunu tutmaya devam
edebilir**. Yeni bir sunucu başlatırsın, sağlık denetimi 200 döner, ama
istekleri hâlâ eski kod cevaplar — düzeltmen çalışmıyor sanırsın. Bir
düzeltmeyi HTTP üzerinden doğrularken önce tek dinleyici olduğunu kontrol et:

```bash
netstat -ano | grep ":8000" | grep LISTENING
```

İki satır görüyorsan yetim bir işçi vardır; ölçtüğün şey bayat sunucudur.
Aynı doğrulamayı süreç içinde de yap (ilgili fonksiyonu doğrudan çağır);
iki yöntem aynı sonucu vermiyorsa sunucuya değil, koda güven.

## 5. SSR'de rastgele kimlik üretme

`crypto.randomUUID()` sunucu ve istemcide farklı değer üretir → React
hydration uyuşmazlığı. Başlangıç kimlikleri deterministik olmalı
(`adim-1`, `adim-2` …). Kullanıcı etkileşimiyle **sonradan** eklenen
satırlarda rastgele kimlik güvenlidir; o kod yalnızca istemcide çalışır.

## 6. Şablonlar salt okunur

`templates/` altındaki dosyaların üzerine hiçbir koşulda yazma. Her zaman
kopya üzerinde çalış. Şablon Excel'de açılıp kaydedilmişse çizim nesneleri
zaten kaybolmuştur; çıktı doğrulayıcı bunu yakalar ve üretim durur.

## 7. Metni sessizce kırpma

Sarı alan sınırı `lib/types.ts` içindeki `SARI_ALAN_SINIRI` ile tanımlıdır.
Aşıldığında program metni kırpmaz — üretimi durdurup kullanıcıdan kısaltma
ister. Fabrikada eksik okunan bir talimat, sığdırılmış bir talimattan çok
daha pahalıdır. Sınırı değiştirirken README'yi de güncelle; ikisi bir kez
birbirinden ayrı düştü.

## 8. Testler ve doğrulama

```bash
python -m pytest -q
```

```bash
cd web && npx playwright test
```

Playwright **iki** sunucu birden başlatır (uvicorn + Next.js); üretim
akışları gerçek motora karşı koşar. Yalnızca Next.js başlatmak, xlsx üreten
akışları sessizce test dışı bırakır. Next 16 aynı dizinden ikinci bir dev
sunucusuna izin vermez — başka bir `next dev` çalışıyorsa önce onu durdur.

## 9. Arayüz kuralları

Yığın **Next.js + TypeScript + Tailwind + shadcn/ui**; Python HTML sunmaz,
yalnızca JSON ve xlsx döndürür. Tasarım kararları tahminle seçilmez:
`design-system/kalite-dokuman-uretici/MASTER.md` bağlayıcıdır, sayfaya özel
dosyalar (`design-system/pages/*.md`) onu ezer.

Erişilebilirlik, bu projede test edilen bir gereksinim:

- Her girdinin görünür etiketi ve `htmlFor`/`id` eşleşmesi olmalı
  (`components/ortak/alan.tsx`). Tablo hücrelerinde `aria-label` kullan.
- Sürükleme tek taşıma yolu olamaz (WCAG 2.2). Kontrol adımı kartlarında
  yukarı/aşağı düğmeleri sürüklemenin tek-işaretçili alternatifidir.
- Doğrulama hatası yalnızca toast ile verilmez; toast odak almaz ve kaybolur.
  Hata, odaklanabilir `role="alert"` bölgesinde duyurulur
  (`components/ortak/eylem-cubugu.tsx`).
- Hareket eklerken `useReducedMotion()` kontrol et ve bir görünümde
  1-2 öğeden fazlasını canlandırma.

## 10. Kod dili

Tanımlayıcılar ve yorumlar Türkçedir (`hazirlayan`, `dosyaAdi`, `uretiliyor`).
Yeni kod çevredeki dile uyar. Yorumlar "ne" değil "neden" anlatır — bu
dosyadaki kuralların çoğu kod içinde de kısa birer yorum olarak yaşar.
