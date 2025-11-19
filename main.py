"""
Brightness Guard - Otomatik Ekran Karartma Uygulaması
Multi-monitor destekli - Her ekranı bağımsız kontrol eder
"""
import time
import logging
import sys
import os
import signal
import atexit
from brightness_controller import BrightnessController
from screen_analyzer import ScreenAnalyzer
from gui import SystemTrayGUI

# Windows konsol için UTF-8 kodlaması
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brightness_guard.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BrightnessGuard:
    def __init__(self):
        """Ana uygulama sınıfı - Multi-monitor destekli"""
        self.brightness_controller = BrightnessController()
        self.screen_analyzer = ScreenAnalyzer(sample_size=20)  # Daha küçük sample = daha hızlı
        self.gui = None

        # Ayarlar
        self.brightness_threshold = 70  # Parlaklık eşiği (0-100)
        self.target_brightness = 30     # Hedef parlaklık (karartma seviyesi)
        self.check_interval = 0.05      # Kontrol aralığı (saniye) - 0.05 = 50ms, çok responsive!

        # Durum
        self.is_running = False
        self.is_active = True
        self.is_cleaning_up = False  # Temizlik yapılıyor mu?
        self.monitor_states = {}  # Her monitörün durumunu takip et

        monitor_count = self.screen_analyzer.get_monitor_count()
        logger.info("=" * 60)
        logger.info("Brightness Guard başlatıldı - Multi-Monitor Modu")
        logger.info("=" * 60)
        logger.info(f"Tespit edilen monitör sayısı: {monitor_count}")
        logger.info(f"Parlaklık eşiği: {self.brightness_threshold}%")
        logger.info(f"Hedef parlaklık: {self.target_brightness}%")
        logger.info(f"Kontrol aralığı: {self.check_interval*1000:.0f}ms (Süper responsive!)")
        logger.info("=" * 60)

    def check_and_adjust(self):
        """Tüm monitörleri kontrol et ve gerekirse parlaklığı ayarla"""
        try:
            # Tüm monitörleri analiz et
            results = self.screen_analyzer.analyze_all_monitors(threshold=self.brightness_threshold)

            for monitor_index, is_bright, brightness_value in results:
                # Bu monitörün önceki durumunu al
                was_dimmed = self.monitor_states.get(monitor_index, False)

                # Ekran parlaksa ve henüz karartılmamışsa
                if is_bright and not was_dimmed:
                    logger.info(f"⚡ Monitör {monitor_index+1}: Parlak ekran tespit edildi! "
                               f"Parlaklık: {brightness_value:.1f}%")
                    logger.info(f"   → Monitör {monitor_index+1} parlaklığı {self.target_brightness}%'ye düşürülüyor...")

                    success = self.brightness_controller.dim_screen(
                        self.target_brightness,
                        monitor_index
                    )

                    if success:
                        self.monitor_states[monitor_index] = True
                        logger.info(f"   ✓ Monitör {monitor_index+1} karartıldı")
                        if self.gui:
                            self.gui.update_icon(self.is_active, any(self.monitor_states.values()))

                # Ekran artık parlak değilse ve karartılmışsa
                elif not is_bright and was_dimmed:
                    logger.info(f"⚡ Monitör {monitor_index+1}: Normal ekran. Parlaklık: {brightness_value:.1f}%")
                    logger.info(f"   → Monitör {monitor_index+1} orijinal parlaklığa dönüyor...")

                    success = self.brightness_controller.restore_brightness(monitor_index)

                    if success:
                        self.monitor_states[monitor_index] = False
                        logger.info(f"   ✓ Monitör {monitor_index+1} parlaklık geri yüklendi")
                        if self.gui:
                            self.gui.update_icon(self.is_active, any(self.monitor_states.values()))

        except Exception as e:
            logger.error(f"Kontrol sırasında hata: {e}", exc_info=True)

    def activate(self):
        """Korumayı aktif et"""
        self.is_active = True
        logger.info("✓ Brightness Guard aktif edildi")
        if self.gui:
            self.gui.update_icon(self.is_active, any(self.monitor_states.values()))

    def deactivate(self):
        """Korumayı devre dışı bırak"""
        self.is_active = False

        # Karartılmış tüm monitörleri geri yükle
        for monitor_index, is_dimmed in self.monitor_states.items():
            if is_dimmed:
                self.brightness_controller.restore_brightness(monitor_index)
                self.monitor_states[monitor_index] = False

        logger.info("○ Brightness Guard devre dışı bırakıldı")
        if self.gui:
            self.gui.update_icon(self.is_active, False)

    def run(self):
        """Ana döngü - Süper responsive!"""
        self.is_running = True

        # GUI'yi başlat
        self.gui = SystemTrayGUI(self)
        gui_thread = self.gui.start()

        logger.info("🚀 Brightness Guard çalışıyor (Sistem tepsisinde)")
        logger.info("⚙️  Ayarlar için sistem tepsisindeki ikona sağ tıklayın")
        logger.info("")

        try:
            iteration = 0
            while self.is_running:
                if self.is_active:
                    self.check_and_adjust()

                # Her 100 iterasyonda bir (yaklaşık 5 saniyede) sessizce döngüde olduğumuzu belirt
                iteration += 1
                if iteration % 100 == 0:
                    logger.debug(f"Döngü aktif - {iteration} iterasyon tamamlandı")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("⏸️  Kullanıcı tarafından durduruldu")
            self.stop()

        # GUI thread'inin bitmesini bekle
        if gui_thread.is_alive():
            gui_thread.join(timeout=2)

    def stop(self):
        """Uygulamayı durdur"""
        self.is_running = False

    def cleanup(self):
        """Temizleme işlemi - her durumda çağrılır"""
        if self.is_cleaning_up:
            return  # Zaten temizlik yapılıyor, tekrar yapma

        self.is_cleaning_up = True
        logger.info("🧹 Temizlik başlatılıyor...")
        self.is_running = False

        # ÖNCE tüm karartılmış monitörleri geri yükle
        logger.info("🔄 Monitör parlaklıkları geri yükleniyor...")
        restored_count = 0

        for monitor_index in range(3):  # 3 monitör var
            if self.monitor_states.get(monitor_index, False):
                try:
                    self.brightness_controller.restore_brightness(monitor_index)
                    logger.info(f"   ✓ Monitör {monitor_index+1} geri yüklendi")
                    restored_count += 1
                except Exception as e:
                    logger.error(f"   ✗ Monitör {monitor_index+1} geri yüklenemedi: {e}")

        if restored_count > 0:
            logger.info(f"✅ {restored_count} monitör parlaklığı geri yüklendi")
        else:
            logger.info("ℹ️  Geri yüklenecek monitör bulunamadı")

        logger.info("👋 Brightness Guard kapatıldı")


def main():
    """Ana fonksiyon"""
    print("=" * 70)
    print("  Brightness Guard - Multi-Monitor Otomatik Ekran Karartma")
    print("=" * 70)
    print()
    print("✨ Özellikler:")
    print("  • Her monitörü bağımsız kontrol eder")
    print("  • Sadece beyaz/parlak ekranı karartır")
    print("  • Süper responsive (50ms kontrol aralığı)")
    print("  • Göz sağlığınızı korur")
    print()
    print("🎯 Uygulama sistem tepsisinde çalışacak")
    print("⚙️  Ayarlar için sistem tepsisindeki ikona sağ tıklayın")
    print()
    print("⏹️  Çıkmak için Ctrl+C veya sistem tepsisinden çıkış yapın")
    print("=" * 70)
    print()

    app = BrightnessGuard()

    # Cleanup fonksiyonunu kaydet - uygulama her şekilde kapanırsa çalışır
    def emergency_cleanup(*args):
        """Acil durum temizliği - her durumda çalışır"""
        logger.info("⚠️  Acil durum temizliği başlatıldı")
        app.cleanup()

    # atexit: Normal kapanışta çalışır
    atexit.register(app.cleanup)

    # signal: Ctrl+C, kill, vb. sinyallerde çalışır
    signal.signal(signal.SIGINT, emergency_cleanup)
    signal.signal(signal.SIGTERM, emergency_cleanup)

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("⏸️  Kullanıcı tarafından durduruldu (Ctrl+C)")
        app.cleanup()
    except Exception as e:
        logger.error(f"❌ Beklenmeyen hata: {e}", exc_info=True)
        print(f"\n❌ Hata oluştu: {e}")
        print("📋 Detaylar için brightness_guard.log dosyasını kontrol edin")
        app.cleanup()
    finally:
        # Her durumda temizlik yap
        app.cleanup()


if __name__ == "__main__":
    main()
