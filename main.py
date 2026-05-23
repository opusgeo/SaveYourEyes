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
        self.screen_analyzer = ScreenAnalyzer(sample_size=20)
        self.gui = None

        # Ayarlar
        self.brightness_threshold = 70  # Normal modda beyaz piksel eşiği (0-100)
        self.target_brightness = 30     # Hedef parlaklık (karartma seviyesi)
        self.check_interval = 0.05      # Kontrol aralığı (saniye)

        # Mod: 'night' = her zaman %30, 'normal' = ekran %50 beyazsa %30
        self.mode = 'night'

        # Durum
        self.is_running = False
        self.is_active = True
        self.is_cleaning_up = False
        self.monitor_states = {}

        monitor_count = self.screen_analyzer.get_monitor_count()
        logger.info("=" * 60)
        logger.info("Brightness Guard başlatıldı - Multi-Monitor Modu")
        logger.info("=" * 60)
        logger.info(f"Tespit edilen monitör sayısı: {monitor_count}")
        logger.info(f"Başlangıç modu: Gece Modu")
        logger.info(f"Hedef parlaklık: {self.target_brightness}%")
        logger.info(f"Kontrol aralığı: {self.check_interval*1000:.0f}ms")
        logger.info("=" * 60)

    def set_mode(self, mode):
        """Modu değiştir: 'night' veya 'normal'"""
        self.mode = mode
        monitor_count = self.screen_analyzer.get_monitor_count()

        if mode == 'night':
            logger.info("🌙 Gece Modu aktif — tüm monitörler %30'a kısıldı")
            for i in range(monitor_count):
                self.brightness_controller.dim_screen(self.target_brightness, i)
                self.monitor_states[i] = True
        else:
            logger.info("☀️ Normal Mod aktif — beyaz ekran takibi başladı")
            for i in range(monitor_count):
                if self.monitor_states.get(i, False):
                    self.brightness_controller.restore_brightness(i)
                    self.monitor_states[i] = False

        if self.gui:
            self.gui.update_icon(self.is_active, self.mode, any(self.monitor_states.values()))

    def check_and_adjust(self):
        """Normal modda ekranları izle ve gerekirse parlaklığı ayarla"""
        if self.mode == 'night':
            return  # Gece modunda analiz gerekmez

        try:
            monitor_count = self.screen_analyzer.get_monitor_count()
            for i in range(monitor_count):
                img = self.screen_analyzer.capture_monitor(i)
                was_dimmed = self.monitor_states.get(i, False)

                # Ekranın %50'sinden fazlası beyaz/açık renkli mi?
                is_white = self.screen_analyzer.is_light_color_dominant(img, threshold=self.brightness_threshold)

                if is_white and not was_dimmed:
                    success = self.brightness_controller.dim_screen(self.target_brightness, i)
                    if success:
                        self.monitor_states[i] = True
                        logger.info(f"Monitör {i+1}: Beyaz ekran tespit edildi → %{self.target_brightness}'e düşürüldü")
                        if self.gui:
                            self.gui.update_icon(self.is_active, self.mode, any(self.monitor_states.values()))

                elif not is_white and was_dimmed:
                    success = self.brightness_controller.restore_brightness(i)
                    if success:
                        self.monitor_states[i] = False
                        logger.info(f"Monitör {i+1}: Normal ekran → parlaklık geri yüklendi")
                        if self.gui:
                            self.gui.update_icon(self.is_active, self.mode, any(self.monitor_states.values()))

        except Exception as e:
            logger.error(f"Kontrol sırasında hata: {e}", exc_info=True)

    def activate(self):
        """Korumayı aktif et"""
        self.is_active = True
        logger.info("✓ Brightness Guard aktif edildi")
        if self.gui:
            self.gui.update_icon(self.is_active, self.mode, any(self.monitor_states.values()))

    def deactivate(self):
        """Korumayı devre dışı bırak"""
        self.is_active = False
        for monitor_index, is_dimmed in self.monitor_states.items():
            if is_dimmed:
                self.brightness_controller.restore_brightness(monitor_index)
                self.monitor_states[monitor_index] = False
        logger.info("○ Brightness Guard devre dışı bırakıldı")
        if self.gui:
            self.gui.update_icon(self.is_active, self.mode, False)

    def run(self):
        """Ana döngü - Süper responsive!"""
        self.is_running = True

        # GUI'yi başlat
        self.gui = SystemTrayGUI(self)
        gui_thread = self.gui.start()

        # Başlangıç modu: Gece Modu
        self.set_mode('night')

        logger.info("🚀 Brightness Guard çalışıyor (Sistem tepsisinde)")
        logger.info("⚙️  Mod değiştirmek için sistem tepsisindeki ikona sağ tıklayın")
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
