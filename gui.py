"""
Sistem tepsisi GUI modülü
"""
import pystray
from PIL import Image, ImageDraw
import threading
import logging

logger = logging.getLogger(__name__)


class SystemTrayGUI:
    def __init__(self, app):
        """
        Args:
            app: Ana uygulama referansı
        """
        self.app = app
        self.icon = None
        self.running = False

    def create_icon_image(self, color="white"):
        """Sistem tepsisi ikonu oluştur"""
        # 64x64 basit bir ikon oluştur
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)

        # Güneş şekli çiz (parlaklık sembolü)
        if color == "green":
            fill_color = (0, 255, 0)  # Aktif - yeşil
        elif color == "orange":
            fill_color = (255, 165, 0)  # Karartılmış - turuncu
        else:
            fill_color = (255, 255, 255)  # Normal - beyaz

        # Daire çiz
        draw.ellipse([16, 16, 48, 48], fill=fill_color, outline=fill_color)

        # Işınlar
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            x1 = 32 + int(20 * math.cos(rad))
            y1 = 32 + int(20 * math.sin(rad))
            x2 = 32 + int(28 * math.cos(rad))
            y2 = 32 + int(28 * math.sin(rad))
            draw.line([x1, y1, x2, y2], fill=fill_color, width=2)

        return image

    def update_icon(self, is_active, is_dimmed):
        """İkon rengini güncelle"""
        if self.icon is not None:
            if is_dimmed:
                self.icon.icon = self.create_icon_image("orange")
            elif is_active:
                self.icon.icon = self.create_icon_image("green")
            else:
                self.icon.icon = self.create_icon_image("white")

    def on_quit(self, icon, item):
        """Uygulamayı kapat ve parlaklıkları geri yükle"""
        logger.info("📱 Sistem tepsisinden kapatma isteği")
        self.running = False

        # Önce parlaklıkları geri yükle
        self.app.cleanup()

        # Sonra ikonu kapat
        icon.stop()

    def on_toggle(self, icon, item):
        """Korumayı aç/kapat"""
        if self.app.is_active:
            self.app.deactivate()
            logger.info("Koruma devre dışı")
        else:
            self.app.activate()
            logger.info("Koruma etkin")

    def on_settings(self, icon, item):
        """Ayarlar penceresi aç"""
        # Basit bir ayarlar dialogu
        import tkinter as tk
        from tkinter import ttk

        settings_window = tk.Tk()
        settings_window.title("Brightness Guard - Ayarlar")
        settings_window.geometry("400x350")
        settings_window.resizable(False, False)

        # Stil
        style = ttk.Style()
        style.theme_use('clam')

        # Ana frame
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Başlık
        title = ttk.Label(main_frame, text="Brightness Guard Ayarları",
                         font=('Segoe UI', 14, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Parlaklık eşiği
        ttk.Label(main_frame, text="Parlaklık Eşiği:",
                 font=('Segoe UI', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        threshold_var = tk.IntVar(value=self.app.brightness_threshold)
        threshold_scale = ttk.Scale(main_frame, from_=0, to=100,
                                   variable=threshold_var, orient=tk.HORIZONTAL)
        threshold_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        threshold_label = ttk.Label(main_frame, text=f"{threshold_var.get()}%")
        threshold_label.grid(row=2, column=1, sticky=tk.W)

        def update_threshold_label(*args):
            threshold_label.config(text=f"{threshold_var.get()}%")
        threshold_var.trace('w', update_threshold_label)

        # Hedef parlaklık
        ttk.Label(main_frame, text="Hedef Parlaklık:",
                 font=('Segoe UI', 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        target_var = tk.IntVar(value=self.app.target_brightness)
        target_scale = ttk.Scale(main_frame, from_=0, to=100,
                                variable=target_var, orient=tk.HORIZONTAL)
        target_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        target_label = ttk.Label(main_frame, text=f"{target_var.get()}%")
        target_label.grid(row=4, column=1, sticky=tk.W)

        def update_target_label(*args):
            target_label.config(text=f"{target_var.get()}%")
        target_var.trace('w', update_target_label)

        # Kontrol aralığı
        ttk.Label(main_frame, text="Kontrol Aralığı (ms):",
                 font=('Segoe UI', 10)).grid(row=5, column=0, sticky=tk.W, pady=5)
        interval_var = tk.DoubleVar(value=self.app.check_interval * 1000)  # saniye -> ms
        interval_scale = ttk.Scale(main_frame, from_=10, to=1000,
                                  variable=interval_var, orient=tk.HORIZONTAL)
        interval_scale.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        interval_label = ttk.Label(main_frame, text=f"{int(interval_var.get())}ms")
        interval_label.grid(row=6, column=1, sticky=tk.W)

        def update_interval_label(*args):
            interval_label.config(text=f"{int(interval_var.get())}ms")
        interval_var.trace('w', update_interval_label)

        # Bilgi
        info_text = ("Parlaklık Eşiği: Ekran bu değerin üzerinde parlaksa karartma aktif olur.\n\n"
                    "Hedef Parlaklık: Ekran karartıldığında monitör bu parlaklığa ayarlanır.\n\n"
                    "Kontrol Aralığı: Ekranın ne sıklıkla kontrol edileceği (ms). "
                    "Düşük değer = daha responsive (önerilen: 50ms)")
        info_label = ttk.Label(main_frame, text=info_text,
                             font=('Segoe UI', 9), foreground='gray',
                             wraplength=350, justify=tk.LEFT)
        info_label.grid(row=7, column=0, columnspan=2, pady=(15, 10))

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        def apply_settings():
            """Ayarları uygula ama pencereyi kapatma"""
            self.app.brightness_threshold = threshold_var.get()
            self.app.target_brightness = target_var.get()
            self.app.check_interval = interval_var.get() / 1000  # ms -> saniye
            logger.info(f"✓ Ayarlar uygulandı: Eşik={self.app.brightness_threshold}%, "
                       f"Hedef={self.app.target_brightness}%, Aralık={self.app.check_interval*1000:.0f}ms")

            # Başarı mesajı göster
            status_label = ttk.Label(main_frame, text="✓ Ayarlar uygulandı!",
                                    foreground='green', font=('Segoe UI', 9, 'bold'))
            status_label.grid(row=9, column=0, columnspan=2, pady=(5, 0))

            # 2 saniye sonra mesajı kaldır
            settings_window.after(2000, lambda: status_label.destroy())

        def save_and_close():
            """Ayarları kaydet ve pencereyi kapat"""
            apply_settings()
            settings_window.after(500, settings_window.destroy)  # 500ms sonra kapat

        apply_btn = ttk.Button(button_frame, text="Uygula", command=apply_settings, width=15)
        apply_btn.pack(side=tk.LEFT, padx=5)

        save_btn = ttk.Button(button_frame, text="Kaydet ve Kapat", command=save_and_close, width=15)
        save_btn.pack(side=tk.LEFT, padx=5)

        settings_window.mainloop()

    def create_menu(self):
        """Sistem tepsisi menüsü oluştur"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda text: f"{'✓' if self.app.is_active else '○'} Koruma Aktif",
                self.on_toggle,
                default=True
            ),
            pystray.MenuItem("Ayarlar", self.on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Çıkış", self.on_quit)
        )

    def run(self):
        """Sistem tepsisi ikonunu çalıştır"""
        self.running = True
        self.icon = pystray.Icon(
            "brightness_guard",
            self.create_icon_image("green"),
            "Brightness Guard",
            self.create_menu()
        )

        logger.info("Sistem tepsisi başlatılıyor...")
        self.icon.run()

    def start(self):
        """GUI'yi ayrı thread'de başlat"""
        gui_thread = threading.Thread(target=self.run, daemon=True)
        gui_thread.start()
        return gui_thread
