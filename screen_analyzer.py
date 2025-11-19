"""
Ekran görüntüsünü analiz eden modül - Multi-monitor destekli
Beyaz ve açık tonları tespit eder, her ekranı ayrı ayrı kontrol eder
"""
import numpy as np
from PIL import Image
import mss
import logging

logger = logging.getLogger(__name__)


class ScreenAnalyzer:
    def __init__(self, sample_size=30):
        """
        Args:
            sample_size: Analiz için örnekleme boyutu (performans için küçültüldü)
        """
        self.sample_size = sample_size
        self.sct = mss.mss()
        self.monitors = self.sct.monitors[1:]  # İlk eleman tüm ekranlar, onu atlıyoruz
        logger.info(f"{len(self.monitors)} monitör tespit edildi")
        for i, mon in enumerate(self.monitors, 1):
            logger.info(f"Monitör {i}: {mon['width']}x{mon['height']} @ ({mon['left']}, {mon['top']})")

    def capture_monitor(self, monitor_index):
        """
        Belirli bir monitörün ekran görüntüsünü al

        Args:
            monitor_index: Monitör indeksi (0'dan başlar)

        Returns:
            PIL Image veya None
        """
        try:
            if monitor_index >= len(self.monitors):
                return None

            monitor = self.monitors[monitor_index]
            sct_img = self.sct.grab(monitor)

            # MSS screenshot'ı PIL Image'e çevir
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            return img

        except Exception as e:
            logger.error(f"Monitör {monitor_index} görüntüsü alınamadı: {e}")
            return None

    def analyze_brightness(self, image=None):
        """
        Görüntünün ortalama parlaklığını analiz et

        Returns:
            float: 0-100 arası parlaklık yüzdesi
        """
        if image is None:
            return 50  # Varsayılan değer

        try:
            # Görüntüyü küçült (performans için)
            small_image = image.resize((self.sample_size, self.sample_size), Image.LANCZOS)

            # NumPy array'e çevir
            pixels = np.array(small_image)

            # RGB kanallarının ortalamasını al (parlaklık)
            brightness = np.mean(pixels)

            # 0-100 arasına normalize et
            brightness_percent = (brightness / 255) * 100

            return brightness_percent

        except Exception as e:
            logger.error(f"Parlaklık analizi başarısız: {e}")
            return 50

    def detect_white_screen(self, image, threshold=70):
        """
        Beyaz/açık ekran tespit et

        Args:
            image: PIL Image objesi
            threshold: Parlaklık eşiği (0-100), varsayılan 70

        Returns:
            tuple: (is_bright, brightness_value)
        """
        if image is None:
            return False, 0

        brightness = self.analyze_brightness(image)
        is_bright = brightness > threshold

        return is_bright, brightness

    def is_light_color_dominant(self, image, threshold=70):
        """
        Açık renklerin görüntüde baskın olup olmadığını kontrol et

        Args:
            image: PIL Image objesi
            threshold: Açık renk eşiği (0-100)

        Returns:
            bool: Açık renkler baskınsa True
        """
        if image is None:
            return False

        try:
            # Görüntüyü küçült
            small_image = image.resize((self.sample_size, self.sample_size), Image.LANCZOS)
            pixels = np.array(small_image).reshape(-1, 3)

            # Her pikselin parlaklığını hesapla
            brightness_values = np.mean(pixels, axis=1)

            # Açık piksellerin yüzdesini hesapla
            light_threshold = (threshold / 100) * 255
            light_pixels = np.sum(brightness_values > light_threshold)
            total_pixels = len(brightness_values)

            light_percentage = (light_pixels / total_pixels) * 100

            # Eğer görüntünün %50'sinden fazlası açıksa
            is_light = light_percentage > 50

            return is_light

        except Exception as e:
            logger.error(f"Renk analizi başarısız: {e}")
            return False

    def analyze_all_monitors(self, threshold=70):
        """
        Tüm monitörleri analiz et ve her birinin durumunu döndür

        Args:
            threshold: Parlaklık eşiği

        Returns:
            list: Her monitör için (monitor_index, is_bright, brightness_value) tuple'ları
        """
        results = []

        for i in range(len(self.monitors)):
            try:
                # Monitör görüntüsünü al
                img = self.capture_monitor(i)

                if img is None:
                    results.append((i, False, 0))
                    continue

                # Parlaklık analizi
                is_bright, brightness = self.detect_white_screen(img, threshold)

                # Açık renk analizi
                is_light = self.is_light_color_dominant(img, threshold)

                # İkisinden biri True ise parlak kabul et
                final_is_bright = is_bright or is_light

                results.append((i, final_is_bright, brightness))

                logger.debug(f"Monitör {i+1}: Parlaklık={brightness:.1f}%, Parlak={final_is_bright}")

            except Exception as e:
                logger.error(f"Monitör {i} analizi başarısız: {e}")
                results.append((i, False, 0))

        return results

    def get_monitor_count(self):
        """Monitör sayısını döndür"""
        return len(self.monitors)
