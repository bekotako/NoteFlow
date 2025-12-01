import ctypes
import sys
import os
import threading
import time
import json
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# --- AYARLAR ---
EC_SC = 0x66
EC_DATA = 0x62
FAN_REG = 0x2F
CONFIG_FILE = "settings.json"

# --- TEMA ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- ÇOKLU DİL PAKETİ ---
LANGUAGES = {
    "TR": {
        "header_title": "SYSTEM",
        "header_sub": "FAN CONTROLLER",
        "card_title": "AKTİF MOD",
        "btn_auto": "🛡️ OTOMATİK", "sub_auto": "Sistem Varsayılanı",
        "btn_silent": "🌙 SESSİZ", "sub_silent": "Minimum Ses (Seviye 1)",
        "btn_bal": "⚖️ DENGELİ", "sub_bal": "Günlük Kullanım (Seviye 4)",
        "btn_perf": "🚀 PERFORMANS", "sub_perf": "Yüksek Soğutma (Seviye 7)",
        "btn_turbo": "🔥 TURBO JET", "sub_turbo": "Maksimum Güç (Disengaged)",
        "footer": "Fan Kontrol Sistemi • v3.0",
        "tray_open": "Aç", "tray_exit": "Çıkış",
        "mode_names": {0x80: "OTOMATİK", 1: "SESSİZ", 4: "DENGELİ", 7: "PERFORMANS", 0x40: "TURBO JET"}
    },
    "EN": {
        "header_title": "SYSTEM",
        "header_sub": "FAN CONTROLLER",
        "card_title": "CURRENT MODE",
        "btn_auto": "🛡️ AUTOMATIC", "sub_auto": "System Default",
        "btn_silent": "🌙 SILENT", "sub_silent": "Min Noise (Level 1)",
        "btn_bal": "⚖️ BALANCED", "sub_bal": "Daily Use (Level 4)",
        "btn_perf": "🚀 PERFORMANCE", "sub_perf": "High Cooling (Level 7)",
        "btn_turbo": "🔥 TURBO JET", "sub_turbo": "Max Power (Disengaged)",
        "footer": "Fan Control System • v3.0",
        "tray_open": "Open", "tray_exit": "Exit",
        "mode_names": {0x80: "AUTOMATIC", 1: "SILENT", 4: "BALANCED", 7: "PERFORMANCE", 0x40: "TURBO JET"}
    }
}

# --- DLL YÜKLEME ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

dll_path = resource_path("inpoutx64.dll")
io = None

try:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.user32.MessageBoxW(0, "Lütfen Yönetici Olarak Çalıştırın / Run as Admin", "Error", 0x10)
        sys.exit()
    io = ctypes.windll.LoadLibrary(dll_path)
except Exception:
    sys.exit()

# --- DONANIM KONTROLÜ ---
def wait_write():
    while (io.Inp32(EC_SC) & 2): pass

def write_fan(value):
    try:
        wait_write(); io.Out32(EC_SC, 0x81); wait_write()
        io.Out32(EC_DATA, FAN_REG); wait_write(); io.Out32(EC_DATA, value)
        return True
    except: return False

def create_image(color_hex):
    width = 64; height = 64
    image = Image.new('RGB', (width, height), "#1a1a1a")
    dc = ImageDraw.Draw(image)
    dc.ellipse((10, 10, 54, 54), fill=color_hex)
    return image

# --- AYARLARI YÖNET ---
class ConfigManager:
    @staticmethod
    def load():
        default = {"value": 0x80, "color": "#2ecc71", "lang": "TR"}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return default
        return default

    @staticmethod
    def save(data):
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=4)
        except: pass

# --- ANA UYGULAMA ---
class FanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.cfg = ConfigManager.load()
        self.lang_code = self.cfg.get("lang", "TR")
        self.txt = LANGUAGES[self.lang_code]

        self.title("Fan Controller")
        self.geometry("360x580")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.current_val = self.cfg.get("value", 0x80)
        self.running = True
        self.tray_icon = None

        # Başlangıç Fan Ayarı
        if self.current_val != 0x80:
            write_fan(self.current_val)

        self.setup_ui()
        
        # 2 Saniyelik İnatçı Döngü
        threading.Thread(target=self.persistence_loop, daemon=True).start()

    def setup_ui(self):
        # Ekranı temizle (Dil değişimi için)
        for widget in self.winfo_children():
            widget.destroy()

        # 1. DİL BUTONU (Sağ Üst)
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        
        lang_label = "EN 🇺🇸" if self.lang_code == "TR" else "TR 🇹🇷"
        self.btn_lang = ctk.CTkButton(self.top_bar, text=lang_label, width=50, height=24, 
                                      fg_color="#333", hover_color="#444", 
                                      command=self.toggle_language)
        self.btn_lang.pack(side="right")

        # 2. BAŞLIK
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(5, 10))
        
        ctk.CTkLabel(self.header_frame, text=self.txt["header_title"], font=("Arial", 12, "bold"), text_color="gray").pack()
        ctk.CTkLabel(self.header_frame, text=self.txt["header_sub"], font=("Roboto", 24, "bold"), text_color="white").pack()

        # 3. DURUM KARTI
        self.status_card = ctk.CTkFrame(self, fg_color="#1f1f1f", corner_radius=15, border_width=2, border_color=self.cfg.get("color", "#2ecc71"))
        self.status_card.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(self.status_card, text=self.txt["card_title"], font=("Arial", 10, "bold"), text_color="gray").pack(pady=(15, 0))
        
        # Mod ismini dinamik al
        mode_name = self.txt["mode_names"].get(self.current_val, "UNKNOWN")
        self.lbl_active_mode = ctk.CTkLabel(self.status_card, text=mode_name, font=("Roboto", 22, "bold"), text_color=self.cfg.get("color", "#2ecc71"))
        self.lbl_active_mode.pack(pady=(5, 15))

        # 4. BUTONLAR
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="both", expand=True, padx=25)

        self.add_control_btn(self.txt["btn_auto"], 0x80, "#2ecc71", self.txt["sub_auto"])
        self.add_control_btn(self.txt["btn_silent"], 1, "#3498db", self.txt["sub_silent"])
        self.add_control_btn(self.txt["btn_bal"], 4, "#f1c40f", self.txt["sub_bal"])
        self.add_control_btn(self.txt["btn_perf"], 7, "#e67e22", self.txt["sub_perf"])
        self.add_control_btn(self.txt["btn_turbo"], 0x40, "#e74c3c", self.txt["sub_turbo"])

        # 5. ALT BİLGİ
        ctk.CTkLabel(self, text=self.txt["footer"], font=("Arial", 10), text_color="#444444").pack(side="bottom", pady=15)

    def add_control_btn(self, title, value, color, subtitle):
        ctk.CTkButton(
            self.btn_frame,
            text=f"{title}\n{subtitle}",
            font=("Roboto", 13, "bold"),
            fg_color="#2b2b2b", hover_color="#3a3a3a", text_color="#ecf0f1",
            height=55, corner_radius=10, anchor="w",
            command=lambda: self.set_mode(value, color)
        ).pack(fill="x", pady=5)

    def set_mode(self, val, color):
        self.current_val = val
        mode_name = self.txt["mode_names"].get(val, "UNKNOWN")
        
        # Arayüz
        self.lbl_active_mode.configure(text=mode_name, text_color=color)
        self.status_card.configure(border_color=color)
        
        # Donanım
        write_fan(val)
        
        # Kaydet
        self.cfg["value"] = val
        self.cfg["color"] = color
        ConfigManager.save(self.cfg)

    def toggle_language(self):
        self.lang_code = "EN" if self.lang_code == "TR" else "TR"
        self.txt = LANGUAGES[self.lang_code]
        self.cfg["lang"] = self.lang_code
        ConfigManager.save(self.cfg)
        self.setup_ui() # Arayüzü yeniden çiz

    def persistence_loop(self):
        """2 Saniyelik İnatçı Döngü"""
        while self.running:
            if self.current_val != 0x80:
                write_fan(self.current_val)
            time.sleep(2.0) # 2 Saniye Bekle

    # --- TRAY ---
    def hide_window(self):
        self.withdraw()
        threading.Thread(target=self.start_tray, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        if self.tray_icon: self.tray_icon.stop()

    def quit_app(self, icon=None, item=None):
        self.running = False
        write_fan(0x80)
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit()

    def start_tray(self):
        icon_img = create_image(self.cfg.get("color", "#2ecc71"))
        menu = (item(self.txt["tray_open"], self.show_window, default=True), item(self.txt["tray_exit"], self.quit_app))
        self.tray_icon = pystray.Icon("FanControllerApp", icon_img, "Fan Controller", menu)
        self.tray_icon.run()

if __name__ == "__main__":
    app = FanApp()
    app.mainloop()