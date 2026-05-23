"""
Monitör parlaklığını kontrol eden modül - Multi-monitor destekli
"""
import screen_brightness_control as sbc
import logging

logger = logging.getLogger(__name__)


class BrightnessController:
    def __init__(self):
        self.monitors = []
        self.original_brightness = {}  # Her monitör için orijinal parlaklık
        self.current_brightness = {}   # Her monitör için mevcut parlaklık
        self.is_dimmed = {}            # Her monitör için karartma durumu
        self._initialize()

    def _initialize(self):
        """Monitörleri tespit et ve başlangıç parlaklıklarını al"""
        try:
            # Tüm monitörleri al
            self.monitors = sbc.list_monitors()
            logger.info(f"{len(self.monitors)} monitör tespit edildi: {self.monitors}")

            # Her monitör için parlaklığı al
            brightness_list = sbc.get_brightness()

            if isinstance(brightness_list, list):
                for i, brightness in enumerate(brightness_list):
                    self.original_brightness[i] = 100  # Restore hedefi her zaman %100
                    self.current_brightness[i] = brightness
                    self.is_dimmed[i] = False
                    logger.info(f"Monitör {i} ({self.monitors[i] if i < len(self.monitors) else 'Unknown'}): "
                               f"Mevcut parlaklık {brightness}%, restore hedefi %100")
            else:
                # Tek monitör
                self.original_brightness[0] = 100
                self.current_brightness[0] = brightness_list
                self.is_dimmed[0] = False
                logger.info(f"Mevcut parlaklık: {brightness_list}%, restore hedefi %100")

        except Exception as e:
            logger.error(f"Monitör başlatma hatası: {e}")
            # Varsayılan değerler
            self.original_brightness[0] = 100
            self.current_brightness[0] = 100
            self.is_dimmed[0] = False

    def get_brightness(self, monitor_index=None):
        """
        Monitör parlaklığını al

        Args:
            monitor_index: Monitör indeksi (None ise tüm monitörler)

        Returns:
            int veya list: Parlaklık değeri
        """
        try:
            if monitor_index is None:
                brightness = sbc.get_brightness()
            else:
                if monitor_index < len(self.monitors):
                    brightness = sbc.get_brightness(display=monitor_index)
                else:
                    brightness = self.current_brightness.get(monitor_index, 100)

            return brightness

        except Exception as e:
            logger.error(f"Parlaklık alınamadı (Monitör {monitor_index}): {e}")
            return self.current_brightness.get(monitor_index, 100) if monitor_index is not None else [100]

    def set_brightness(self, value, monitor_index=None):
        """
        Parlaklığı ayarla

        Args:
            value: Parlaklık değeri (0-100)
            monitor_index: Monitör indeksi (None ise tüm monitörler)

        Returns:
            bool: Başarı durumu
        """
        try:
            value = max(0, min(100, value))  # 0-100 arası sınırla

            if monitor_index is None:
                # Tüm monitörler
                sbc.set_brightness(value)
                for i in self.current_brightness.keys():
                    self.current_brightness[i] = value
                logger.info(f"Tüm monitörlerin parlaklığı {value}% olarak ayarlandı")
            else:
                # Belirli bir monitör
                if monitor_index < len(self.monitors):
                    sbc.set_brightness(value, display=monitor_index)
                    self.current_brightness[monitor_index] = value
                    monitor_name = self.monitors[monitor_index] if monitor_index < len(self.monitors) else f"#{monitor_index}"
                    logger.info(f"Monitör {monitor_index} ({monitor_name}) parlaklığı {value}% olarak ayarlandı")
                else:
                    logger.warning(f"Geçersiz monitör indeksi: {monitor_index}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Parlaklık ayarlanamadı (Monitör {monitor_index}): {e}")
            return False

    def dim_screen(self, target_brightness, monitor_index):
        """
        Belirli bir monitörü karart

        Args:
            target_brightness: Hedef parlaklık (0-100)
            monitor_index: Monitör indeksi

        Returns:
            bool: Başarı durumu
        """
        # Orijinal parlaklığı kaydet (ilk kez karartılıyorsa)
        if not self.is_dimmed.get(monitor_index, False):
            current = self.get_brightness(monitor_index)
            if isinstance(current, list) and len(current) > monitor_index:
                self.original_brightness[monitor_index] = current[monitor_index]
            elif not isinstance(current, list):
                self.original_brightness[monitor_index] = current

        success = self.set_brightness(target_brightness, monitor_index)
        if success:
            self.is_dimmed[monitor_index] = True
        return success

    def restore_brightness(self, monitor_index):
        """
        Belirli bir monitörün orijinal parlaklığına dön

        Args:
            monitor_index: Monitör indeksi

        Returns:
            bool: Başarı durumu
        """
        if self.is_dimmed.get(monitor_index, False):
            original = self.original_brightness.get(monitor_index, 100)
            success = self.set_brightness(original, monitor_index)
            if success:
                self.is_dimmed[monitor_index] = False
            return success
        return False

    def get_monitor_count(self):
        """Monitör sayısını döndür"""
        return len(self.monitors)

    def is_monitor_dimmed(self, monitor_index):
        """Monitörün karartılmış olup olmadığını kontrol et"""
        return self.is_dimmed.get(monitor_index, False)
