# Self-Healing Test Otomasyon Projesi

Bu proje, UI test otomasyonunda oluşabilecek locator değişiklikleri ve UI güncelleme sorunları için otomatik olarak iyileştirebilen (self-healing) bir test altyapısı sağlar. Test koşumları sırasında UI elementlerinin değişmesi durumunda alternatif bulma stratejileri kullanarak testlerin sürekli çalışmasını sağlar.

## Özellikler

- **Otomatik İyileştirme (Self-Healing)**: Element bulunamadığında alternatif selector stratejileri kullanır
- **Seçici Veritabanı**: Başarılı seçicileri kaydeder ve sonraki test koşumlarında kullanır
- **Model Tabanlı Tahmin**: Benzer elementleri tanımlayarak alternatif seçiciler önerir
- **Gelişmiş Raporlama**: Self-healing stratejilerinin kullanım ve başarı oranlarını raporlar

## Proje Yapısı

```
self-healing-project/
│
├── features/                  # Behave feature dosyaları
│   ├── environment/           # Behave test ortamı yapılandırması
│   │   └── self_healing.py    # Self-healing mekanizması
│   ├── pages/                 # Page Object Model sınıfları
│   ├── steps/                 # Step tanımlamaları
│   └── *.feature              # Feature dosyaları
│
├── resources/                 # Proje kaynakları
│   └── locator_predict_model.py  # Locator tahmin modeli
│
├── utils/                     # Yardımcı araçlar
│   └── helpers.py             # Yardımcı fonksiyonlar
│
├── archive/                   # Arşivlenmiş kodlar (kullanımdan kaldırılmış)
│
├── locator_db.json            # Locator stratejileri veritabanı
├── requirements.txt           # Bağımlılıklar
└── README.md                  # Bu dosya
```

## Kurulum

1. Projeyi klonlayın:
   ```bash
   git clone <repo-url>
   cd self-healing-project
   ```

2. Sanal ortam oluşturun ve bağımlılıkları yükleyin:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Kullanım

### Testleri Çalıştırma

```bash
# Tüm testleri çalıştır
behave

# Belirli bir feature dosyasını çalıştır
behave features/restaurants.feature

# Belirli bir senaryoyu çalıştır
behave features/restaurants.feature -n "Restaurants page access"
```

## Self-Healing Mekanizması Nasıl Çalışır?

1. **Başlangıç**: Test başlangıcında locator selector veritabanı ve tahmin modeli yüklenir.

2. **Element Bulma Denemeleri**:
   - Önce orijinal seçici denenir
   - Element bulunamazsa, veritabanında kayıtlı başarılı stratejiler denenir
   - Hala bulunamazsa, alternatif stratejiler (ID, CSS, XPath, vb.) kullanılır
   - Son çare olarak model tabanlı tahmin sistemi devreye girer

3. **Başarılı Stratejilerin Kaydedilmesi**: Eğer bir strateji başarılı olursa, gelecekteki kullanım için veritabanına kaydedilir.

### Temel Stratejiler

- **Metin Tabanlı**: Element içindeki metinleri kullanarak bulmaya çalışır
- **Öznitelik Tabanlı**: ID, class, name gibi özelliklere dayanarak eşleştirmeler yapar
- **Form Elemanları İçin Özel Stratejiler**: Giriş alanları, butonlar, formlar için özel stratejiler
- **Element Tipi Tahmini**: Locator ID'sinden elementin türünü tahmin eder
- **CSS/XPath Oluşturma**: Çeşitli CSS ve XPath selektörleri üreterek dener
- **Var Olmayan Filtreleme**: Olmayan elemetleri filtreleyerek gereksiz denemeleri önler

## Lisans

[MIT License](LICENSE) 