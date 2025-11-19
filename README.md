# Brightness Guard - Multi-Monitor Edition

Gözlerinizi korumak için beyaz ve açık tonlardaki ekranları otomatik olarak karartır. **3 monitörünüzü ayrı ayrı kontrol eder!**

## ✨ Özellikler

- **Multi-Monitor Desteği**: Her monitörü bağımsız analiz eder
- **Akıllı Karartma**: Sadece beyaz/parlak olan monitörü karartır
- **Süper Responsive**: 50ms kontrol aralığı (saniyede 20 kez kontrol!)
- **Gerçek Zamanlı**: Ekran parlaklığını gerçek zamanlı analiz eder
- **Monitör Parlaklığı Kontrolü**: DDC/CI protokolü ile gerçek monitör parlaklığını değiştirir
- **Sistem Tepsisinde Çalışır**: Arka planda sessizce görevini yapar
- **Kolay Ayarlar**: GUI ile tüm parametreleri değiştirebilirsiniz

## 🖥️ Monitör Desteği

Tespit edilen monitörleriniz:
- Monitör 1: 1920x1080 @ (3840, 644) - VG249
- Monitör 2: 3840x2160 @ (0, 0) - PA279CV
- Monitör 3: 2560x1440 @ (-2560, 398) - Generic Monitor

Her monitör bağımsız olarak kontrol edilir. Örneğin:
- Monitör 2'de beyaz bir Word belgesi açarsanız → Sadece Monitör 2 kararır
- Monitör 1'de kod editörü açıksa → Monitör 1 normal kalır
- Monitör 3'te Chrome açıksa → Monitör 3 normal kalır

## 🚀 Kurulum

### 1. Python Yükleyin
Python 3.8 veya üzeri gereklidir. [python.org](https://www.python.org/downloads/) adresinden indirin.

### 2. Gerekli Kütüphaneleri Yükleyin

**Otomatik kurulum:**
```bash
install.bat
```

**Manuel kurulum:**
```bash
cd brightness_guard
pip install -r requirements.txt
```

### 3. Uygulamayı Çalıştırın

**Kolay yöntem:**
- `run.bat` dosyasına çift tıklayın

**Komut satırı:**
```bash
python main.py
```

## 🎮 Kullanım

1. Uygulamayı başlatın
2. Sistem tepsisinde güneş ikonu görünecektir
3. İkona sağ tıklayarak:
   - ✓ Korumayı aktif/deaktif edebilirsiniz
   - ⚙️ Ayarlara erişebilirsiniz
   - ❌ Uygulamayı kapatabilirsiniz

## ⚙️ Ayarlar

### Parlaklık Eşiği (0-100%)
Ekran bu değerin üzerinde parlaksa otomatik karartma devreye girer.
- **Varsayılan**: 70%
- **Önerilen**: 60-80% arası
- Daha düşük değer = daha hassas tespit

### Hedef Parlaklık (0-100%)
Ekran karartıldığında monitör bu parlaklığa ayarlanır.
- **Varsayılan**: 30%
- **Önerilen**: 20-40% arası (gece çalışma için)
- **0%** yaparsanız tamamen kararır

### Kontrol Aralığı (10-1000ms)
Ekranın ne sıklıkla kontrol edileceği.
- **Varsayılan**: 50ms (saniyede 20 kez!)
- **Önerilen**: 50-100ms arası
- **10ms**: Ultra responsive, biraz daha CPU kullanımı
- **100ms**: Hala çok hızlı, daha az CPU

## 🔥 Performans

- **CPU Kullanımı**: Çok düşük (~1-2%)
- **RAM**: ~50MB
- **Kontrol Hızı**: 50ms (0.05 saniye)
- **Ekran Analizi**: 20x20 piksel örnekleme (çok hızlı!)

## 🛠️ Teknik Detaylar

### Ekran Analizi
- **MSS**: Multi-monitor ekran görüntüsü almak için
- **PIL/Pillow**: Görüntü işleme
- **NumPy**: Hızlı piksel analizi

### Parlaklık Kontrolü
- **screen-brightness-control**: DDC/CI protokolü ile monitör kontrolü
- Her monitör bağımsız olarak kontrol edilir
- Orijinal parlaklık değerleri saklanır ve geri yüklenir

### Multi-Monitor Desteği
- Her monitör için ayrı ekran görüntüsü
- Her monitör için ayrı parlaklık analizi
- Her monitör için ayrı karartma durumu
- Tüm monitörler paralel olarak kontrol edilir

## 📋 Sorun Giderme

### Monitör parlaklığı değişmiyor
- Monitörünüz DDC/CI protokolünü desteklemiyor olabilir
- Monitör menüsünden DDC/CI'yi aktif edin
- Bazı monitörler (özellikle eski modeller) desteklemeyebilir

### Bir monitör tespit edilmiyor
- `brightness_guard.log` dosyasına bakın
- Monitörün DDC/CI desteği olduğundan emin olun
- Monitör kablosunu kontrol edin (DisplayPort/HDMI)

### Uygulama çok sık değiştiriyor
- Kontrol aralığını artırın (örn. 200ms)
- Parlaklık eşiğini ayarlayın (örn. 75%)

### CPU kullanımı yüksek
- Kontrol aralığını artırın (örn. 100-200ms)
- Varsayılan 50ms zaten çok verimli

## 🎯 Kullanım Senaryoları

### Gece Çalışma
- Eşik: 60%
- Hedef: 20%
- Aralık: 50ms

### Gündüz Kullanım
- Eşik: 80%
- Hedef: 40%
- Aralık: 100ms

### Ultra Hassas
- Eşik: 50%
- Hedef: 15%
- Aralık: 10ms

## 🔄 Otomatik Başlatma

Windows başlangıcında otomatik çalışması için:

1. `Win + R` → `shell:startup` yazın
2. `run.bat` dosyasının kısayolunu buraya atın
3. Windows her açıldığında otomatik başlayacak

## 📊 Log Dosyası

Tüm aktiviteler `brightness_guard.log` dosyasına kaydedilir:
- Monitör tespit bilgileri
- Parlaklık değişimleri
- Hatalar ve uyarılar
- Ayar değişiklikleri

## 🎨 İkon Durumları

- **🟢 Yeşil**: Koruma aktif, tüm monitörler normal
- **🟠 Turuncu**: Koruma aktif, en az bir monitör karartılmış
- **⚪ Beyaz**: Koruma devre dışı

## 📝 Lisans

MIT License - Gözleriniz için geliştirildi ❤️

## 🙏 Teşekkürler

Bu uygulama aşağıdaki kütüphaneleri kullanır:
- Pillow
- screen-brightness-control
- pystray
- numpy
- mss

Göz sağlığınıza dikkat edin! 👀✨
