import ctypes
import sys
import os
import threading
import time
import json
import psutil
import keyboard
import subprocess
import re
import requests
import webbrowser
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import wmi

# --- GITHUB AYARLARI ---
GITHUB_USER = "bekotako" 
GITHUB_REPO = "ThinkPad-Fan-Commander" 
CURRENT_VERSION = "v6.3"

# --- DONANIM AYARLARI ---
EC_SC = 0x66
EC_DATA = 0x62
FAN_REG = 0x2F
BATT_START_REG = 0xB0 
BATT_STOP_REG = 0xB1  
CONFIG_FILE = "settings.json"

# --- TEMA ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- ÇOKLU DİL PAKETİ ---
LANGUAGES = {
    "TR": {
        "app_title": f"ThinkPad Ultimate {CURRENT_VERSION}",
        "tab_dash": "DASHBOARD",
        "tab_fan": "FAN KONTROL",
        "tab_batt": "PİL YÖNETİMİ",
        "tab_set": "AYARLAR",
        "header_sub": "ULTIMATE COMMAND CENTER",
        "lbl_cpu": "İşlemci (CPU)",
        "lbl_ram": "Bellek (RAM)",
        "lbl_disk": "Disk Kullanımı",
        "card_fan": "AKTİF FAN MODU",
        "btn_auto": "🛡️ OTOMATİK", "sub_auto": "Sistem Varsayılanı",
        "btn_silent": "🌙 SESSİZ", "sub_silent": "Minimum Ses",
        "btn_bal": "⚖️ DENGELİ", "sub_bal": "Günlük Kullanım",
        "btn_perf": "🚀 PERFORMANS", "sub_perf": "Yüksek Soğutma",
        "btn_turbo": "🔥 TURBO JET", "sub_turbo": "Maksimum Güç",
        "batt_stats": "CANLI PİL İSTATİSTİKLERİ",
        "lbl_start": "Şarja Başlama:",
        "lbl_stop": "Şarjı Kesme:",
        "preset_travel": "✈️ SEYAHAT (%100)",
        "preset_desktop": "🏠 MASAÜSTÜ (%60)",
        "btn_apply": "AYARLARI UYGULA",
        "lbl_hotkeys": "GLOBAL KISAYOL TUŞLARI",
        "chk_hotkeys": "Kısayolları Aktif Et",
        "hk_info": "Oyun içindeyken fanı kontrol etmenizi sağlar.",
        "hk_list": "Ctrl+Alt+1: Otomatik\nCtrl+Alt+2: Turbo Jet\nCtrl+Alt+3: Sessiz Mod",
        "lbl_system": "SİSTEM ENTEGRASYONU",
        "chk_autostart": "Windows ile Başlat (Görev Zamanlayıcı)",
        "btn_update": "GÜNCELLEMELERİ KONTROL ET",
        "msg_uptodate": "Sürümünüz Güncel!",
        "msg_newvers": "Yeni Sürüm Mevcut! (İndirmek için Tıkla)",
        "msg_error": "Bağlantı Hatası",
        "footer": f"ThinkPad Ultimate System • {CURRENT_VERSION}",
        "mode_names": {128: "OTOMATİK", 1: "SESSİZ", 4: "DENGELİ", 7: "PERFORMANS", 64: "TURBO JET"},
        "tray_open": "Kontrol Panelini Aç",
        "tray_exit": "Çıkış"
    },
    "EN": {
        "app_title": f"ThinkPad Ultimate {CURRENT_VERSION}",
        "tab_dash": "DASHBOARD",
        "tab_fan": "FAN CONTROL",
        "tab_batt": "BATTERY",
        "tab_set": "SETTINGS",
        "header_sub": "ULTIMATE COMMAND CENTER",
        "lbl_cpu": "Processor (CPU)",
        "lbl_ram": "Memory (RAM)",
        "lbl_disk": "Disk Usage",
        "card_fan": "CURRENT FAN MODE",
        "btn_auto": "🛡️ AUTOMATIC", "sub_auto": "System Default",
        "btn_silent": "🌙 SILENT", "sub_silent": "Min Noise",
        "btn_bal": "⚖️ BALANCED", "sub_bal": "Daily Use",
        "btn_perf": "🚀 PERFORMANCE", "sub_perf": "High Cooling",
        "btn_turbo": "🔥 TURBO JET", "sub_turbo": "Max Power",
        "batt_stats": "LIVE BATTERY STATS",
        "lbl_start": "Start Charge:",
        "lbl_stop": "Stop Charge:",
        "preset_travel": "✈️ TRAVEL (100%)",
        "preset_desktop": "🏠 DESKTOP (60%)",
        "btn_apply": "APPLY SETTINGS",
        "lbl_hotkeys": "GLOBAL HOTKEYS",
        "chk_hotkeys": "Enable Hotkeys",
        "hk_info": "Control fan while in-game.",
        "hk_list": "Ctrl+Alt+1: Auto Mode | Ctrl+Alt+2: Turbo",
        "lbl_system": "SYSTEM INTEGRATION",
        "chk_autostart": "Start with Windows (Task Scheduler)",
        "btn_update": "CHECK FOR UPDATES",
        "msg_uptodate": "You are up to date!",
        "msg_newvers": "New Version Available! (Click to Download)",
        "msg_error": "Connection Error",
        "footer": f"ThinkPad Ultimate System • {CURRENT_VERSION}",
        "mode_names": {128: "AUTOMATIC", 1: "SILENT", 4: "BALANCED", 7: "PERFORMANCE", 64: "TURBO JET"},
        "tray_open": "Open Control Panel",
        "tray_exit": "Exit"
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
        ctypes.windll.user32.MessageBoxW(0, "Lütfen Yönetici Olarak Çalıştırın!", "Hata", 0x10)
        sys.exit()
    io = ctypes.windll.LoadLibrary(dll_path)
except Exception:
    sys.exit()

# --- DONANIM ---
def wait_write():
    while (io.Inp32(EC_SC) & 2): pass

def write_ec(reg, value):
    try:
        wait_write(); io.Out32(EC_SC, 0x81); wait_write()
        io.Out32(EC_DATA, reg); wait_write(); io.Out32(EC_DATA, value)
        return True
    except: return False

def create_image(color_hex):
    width = 64; height = 64
    image = Image.new('RGB', (width, height), "#1a1a1a")
    dc = ImageDraw.Draw(image)
    try:
        dc.ellipse((10, 10, 54, 54), fill=color_hex)
    except:
        dc.ellipse((10, 10, 54, 54), fill="#2ecc71") # Hata olursa yeşil yap
    return image

# --- AUTO START ---
def set_autostart_task(enable):
    task_name = "ThinkPadUltimateCenter"
    exe_path = sys.executable 
    if enable:
        cmd = f'schtasks /create /tn "{task_name}" /tr "\'{exe_path}\'" /sc onlogon /rl highest /f'
    else:
        cmd = f'schtasks /delete /tn "{task_name}" /f'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- PİL VERİSİ ---
def get_battery_info(cached_cycle):
    try:
        w = wmi.WMI()
        batt = w.query("SELECT * FROM Win32_Battery")[0]
        percent = batt.EstimatedChargeRemaining
        status_map = {1: "Deşarj", 2: "Şarj", 3: "Dolu", 4: "Düşük", 5: "Kritik"}
        status = status_map.get(batt.BatteryStatus, "-")
        
        health = "N/A"
        try:
            w_deep = wmi.WMI(namespace='root\\wmi')
            static = w_deep.BatteryStaticData()[0]
            full = w_deep.BatteryFullChargedCapacity()[0]
            if static.DesignedCapacity > 0:
                health = f"%{int((full.FullChargedCapacity / static.DesignedCapacity) * 100)}"
        except: pass

        return {"percent": percent, "status": status, "health": health, "cycle": cached_cycle}
    except:
        return {"percent": "--", "status": "--", "health": "--", "cycle": "--"}

# --- KESİN DÖNGÜ SAYISI ---
def get_cycle_count_robust():
    try:
        temp_xml = os.path.join(os.environ['TEMP'], 'batt_report.xml')
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(f'powercfg /batteryreport /xml /output "{temp_xml}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        cycle_count = None
        if os.path.exists(temp_xml):
            with open(temp_xml, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'<CycleCount>(\d+)</CycleCount>', content)
                if match: cycle_count = match.group(1)
            try: os.remove(temp_xml)
            except: pass
        return cycle_count
    except: return None

# --- CONFIG ---
class ConfigManager:
    @staticmethod
    def load():
        default = {"value": 0x80, "color": "#2ecc71", "lang": "TR", "batt_start": 40, "batt_stop": 80, "hotkeys": True, "autostart": False}
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

        self.title(self.txt["app_title"])
        self.geometry("400x750")
        self.resizable(False, False)
        
        # --- TRAY İÇİN KRİTİK AYAR ---
        # Pencere kapatılınca (X) hide_window fonksiyonunu çalıştır
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.current_val = self.cfg.get("value", 0x80)
        self.running = True
        self.tray_icon = None
        self.hotkeys_enabled = self.cfg.get("hotkeys", True)
        self.autostart_enabled = self.cfg.get("autostart", False)
        self.cached_cycle = "..."

        if self.current_val != 0x80: write_ec(FAN_REG, self.current_val)
        self.apply_battery_logic(self.cfg.get("batt_start", 40), self.cfg.get("batt_stop", 80))

        self.setup_ui()
        
        threading.Thread(target=self.persistence_loop, daemon=True).start()
        threading.Thread(target=self.dashboard_loop, daemon=True).start()
        threading.Thread(target=self.fetch_cycle_count, daemon=True).start()
        self.update_battery_ui_loop()
        self.setup_hotkeys()

    def fetch_cycle_count(self):
        val = get_cycle_count_robust()
        self.cached_cycle = val if val else "N/A"

    def apply_battery_logic(self, start, stop):
        write_ec(BATT_STOP_REG, stop)
        time.sleep(0.5)
        write_ec(BATT_START_REG, start)

    def setup_hotkeys(self):
        if self.hotkeys_enabled:
            try:
                keyboard.add_hotkey('ctrl+alt+1', lambda: self.set_mode(0x80, "#2ecc71"))
                keyboard.add_hotkey('ctrl+alt+2', lambda: self.set_mode(0x40, "#e74c3c"))
                keyboard.add_hotkey('ctrl+alt+3', lambda: self.set_mode(1, "#3498db"))
            except: pass
        else:
            keyboard.unhook_all()

    def setup_ui(self):
        for widget in self.winfo_children(): widget.destroy()

        # TOP BAR
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        lang_lbl = "EN 🇺🇸" if self.lang_code == "TR" else "TR 🇹🇷"
        ctk.CTkButton(self.top_bar, text=lang_lbl, width=50, height=24, fg_color="#333", hover_color="#444", 
                      command=self.toggle_language).pack(side="right")

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(0, 10))
        ctk.CTkLabel(self.header_frame, text="THINKPAD", font=("Arial", 12, "bold"), text_color="gray").pack()
        ctk.CTkLabel(self.header_frame, text=self.txt["header_sub"], font=("Roboto", 24, "bold"), text_color="white").pack()

        self.tab_view = ctk.CTkTabview(self, width=360, height=550)
        self.tab_view.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.tab_dash = self.tab_view.add(self.txt["tab_dash"])
        self.tab_fan = self.tab_view.add(self.txt["tab_fan"])
        self.tab_batt = self.tab_view.add(self.txt["tab_batt"])
        self.tab_set = self.tab_view.add(self.txt["tab_set"])

        self.setup_dashboard_tab()
        self.setup_fan_tab()
        self.setup_battery_tab()
        self.setup_settings_tab()

        ctk.CTkLabel(self, text=self.txt["footer"], font=("Arial", 10), text_color="#444444").pack(side="bottom", pady=10)

    # --- DASHBOARD ---
    def setup_dashboard_tab(self):
        ctk.CTkLabel(self.tab_dash, text=self.txt["lbl_cpu"], font=("Roboto", 14, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
        self.bar_cpu = ctk.CTkProgressBar(self.tab_dash, height=15)
        self.bar_cpu.pack(fill="x", padx=20)
        self.lbl_cpu_val = ctk.CTkLabel(self.tab_dash, text="0%", font=("Arial", 12))
        self.lbl_cpu_val.pack(anchor="e", padx=20)

        ctk.CTkLabel(self.tab_dash, text=self.txt["lbl_ram"], font=("Roboto", 14, "bold")).pack(pady=(10, 5), anchor="w", padx=20)
        self.bar_ram = ctk.CTkProgressBar(self.tab_dash, height=15, progress_color="#f1c40f")
        self.bar_ram.pack(fill="x", padx=20)
        self.lbl_ram_val = ctk.CTkLabel(self.tab_dash, text="0%", font=("Arial", 12))
        self.lbl_ram_val.pack(anchor="e", padx=20)

        ctk.CTkLabel(self.tab_dash, text=self.txt["lbl_disk"], font=("Roboto", 14, "bold")).pack(pady=(10, 5), anchor="w", padx=20)
        self.bar_disk = ctk.CTkProgressBar(self.tab_dash, height=15, progress_color="#e74c3c")
        self.bar_disk.pack(fill="x", padx=20)
        self.lbl_disk_val = ctk.CTkLabel(self.tab_dash, text="0%", font=("Arial", 12))
        self.lbl_disk_val.pack(anchor="e", padx=20)

    # --- FAN ---
    def setup_fan_tab(self):
        self.status_card = ctk.CTkFrame(self.tab_fan, fg_color="#1f1f1f", corner_radius=15, border_width=2, border_color=self.cfg.get("color", "#2ecc71"))
        self.status_card.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(self.status_card, text=self.txt["card_fan"], font=("Arial", 10, "bold"), text_color="gray").pack(pady=(15, 0))
        
        mode_name = self.txt["mode_names"].get(self.current_val, "UNKNOWN")
        self.lbl_active_mode = ctk.CTkLabel(self.status_card, text=mode_name, font=("Roboto", 22, "bold"), text_color=self.cfg.get("color", "#2ecc71"))
        self.lbl_active_mode.pack(pady=(5, 15))

        self.btn_frame = ctk.CTkFrame(self.tab_fan, fg_color="transparent")
        self.btn_frame.pack(fill="both", expand=True, padx=15)
        self.add_control_btn(self.txt["btn_auto"], 0x80, "#2ecc71", self.txt["sub_auto"])
        self.add_control_btn(self.txt["btn_silent"], 1, "#3498db", self.txt["sub_silent"])
        self.add_control_btn(self.txt["btn_bal"], 4, "#f1c40f", self.txt["sub_bal"])
        self.add_control_btn(self.txt["btn_perf"], 7, "#e67e22", self.txt["sub_perf"])
        self.add_control_btn(self.txt["btn_turbo"], 0x40, "#e74c3c", self.txt["sub_turbo"])

    # --- BATTERY ---
    def setup_battery_tab(self):
        stats_frame = ctk.CTkFrame(self.tab_batt, fg_color="#1a1a1a", corner_radius=10)
        stats_frame.pack(fill="x", padx=15, pady=(10, 20))
        ctk.CTkLabel(stats_frame, text=self.txt["batt_stats"], font=("Arial", 11, "bold"), text_color="gray").pack(pady=10)
        self.lbl_batt_percent = ctk.CTkLabel(stats_frame, text="-- %", font=("Roboto", 30, "bold"), text_color="#2ecc71")
        self.lbl_batt_percent.pack(pady=(0, 5))
        self.lbl_batt_details = ctk.CTkLabel(stats_frame, text="...", font=("Arial", 12))
        self.lbl_batt_details.pack(pady=(0, 15))

        preset_frame = ctk.CTkFrame(self.tab_batt, fg_color="transparent")
        preset_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(preset_frame, text=self.txt["preset_travel"], width=140, fg_color="#27ae60", hover_color="#2ecc71", command=lambda: self.set_preset(96, 100)).pack(side="left", padx=5)
        ctk.CTkButton(preset_frame, text=self.txt["preset_desktop"], width=140, fg_color="#2980b9", hover_color="#3498db", command=lambda: self.set_preset(50, 60)).pack(side="right", padx=5)

        self.lbl_start = ctk.CTkLabel(self.tab_batt, text=f"{self.txt['lbl_start']} {self.cfg.get('batt_start', 40)}%", font=("Roboto", 12, "bold"))
        self.lbl_start.pack(pady=(15, 0))
        self.slider_start = ctk.CTkSlider(self.tab_batt, from_=40, to=95, number_of_steps=55, command=self.update_batt_labels)
        self.slider_start.set(self.cfg.get("batt_start", 40))
        self.slider_start.pack(fill="x", padx=30, pady=5)

        self.lbl_stop = ctk.CTkLabel(self.tab_batt, text=f"{self.txt['lbl_stop']} {self.cfg.get('batt_stop', 80)}%", font=("Roboto", 12, "bold"))
        self.lbl_stop.pack(pady=(10, 0))
        self.slider_stop = ctk.CTkSlider(self.tab_batt, from_=50, to=100, number_of_steps=50, command=self.update_batt_labels)
        self.slider_stop.set(self.cfg.get("batt_stop", 80))
        self.slider_stop.pack(fill="x", padx=30, pady=5)

        ctk.CTkButton(self.tab_batt, text=self.txt["btn_apply"], fg_color="#8e44ad", hover_color="#9b59b6", height=45, command=self.apply_battery_settings).pack(pady=25, padx=30, fill="x")

    # --- SETTINGS ---
    def setup_settings_tab(self):
        ctk.CTkLabel(self.tab_set, text=self.txt["lbl_hotkeys"], font=("Roboto", 16, "bold")).pack(pady=(20, 10))
        self.switch_hotkey = ctk.CTkSwitch(self.tab_set, text=self.txt["chk_hotkeys"], command=self.toggle_hotkeys)
        if self.cfg.get("hotkeys", True): self.switch_hotkey.select()
        else: self.switch_hotkey.deselect()
        self.switch_hotkey.pack(pady=5)
        
        ctk.CTkLabel(self.tab_set, text=self.txt["hk_info"], font=("Arial", 11), text_color="gray").pack()
        info_frame = ctk.CTkFrame(self.tab_set, fg_color="#1a1a1a", corner_radius=8)
        info_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(info_frame, text=self.txt["hk_list"], font=("Consolas", 11), justify="left").pack(pady=10, padx=10)

        ctk.CTkLabel(self.tab_set, text=self.txt["lbl_system"], font=("Roboto", 16, "bold")).pack(pady=(20, 10))
        self.switch_auto = ctk.CTkSwitch(self.tab_set, text=self.txt["chk_autostart"], command=self.toggle_autostart)
        if self.cfg.get("autostart", False): self.switch_auto.select()
        else: self.switch_auto.deselect()
        self.switch_auto.pack(pady=5)

        ctk.CTkButton(self.tab_set, text=self.txt["btn_update"], fg_color="#34495e", hover_color="#2c3e50", command=self.check_updates).pack(pady=20)

    def add_control_btn(self, title, value, color, subtitle):
        ctk.CTkButton(self.btn_frame, text=f"{title}\n{subtitle}", font=("Roboto", 13, "bold"), fg_color="#2b2b2b", hover_color="#3a3a3a", text_color="#ecf0f1", height=50, corner_radius=10, anchor="w", command=lambda: self.set_mode(value, color)).pack(fill="x", pady=5)

    def set_mode(self, val, color):
        self.current_val = val
        mode_name = self.txt["mode_names"].get(val, "UNKNOWN")
        self.lbl_active_mode.configure(text=mode_name, text_color=color)
        self.status_card.configure(border_color=color)
        write_ec(FAN_REG, val)
        self.cfg["value"] = val
        self.cfg["color"] = color
        ConfigManager.save(self.cfg)

    def update_batt_labels(self, value=None):
        s_val = int(self.slider_start.get())
        e_val = int(self.slider_stop.get())
        if s_val >= e_val: self.slider_stop.set(s_val + 1)
        self.lbl_start.configure(text=f"{self.txt['lbl_start']} {int(self.slider_start.get())}%")
        self.lbl_stop.configure(text=f"{self.txt['lbl_stop']} {int(self.slider_stop.get())}%")

    def set_preset(self, start, stop):
        self.slider_start.set(start)
        self.slider_stop.set(stop)
        self.update_batt_labels()
        self.apply_battery_settings()

    def apply_battery_settings(self):
        s = int(self.slider_start.get())
        e = int(self.slider_stop.get())
        self.apply_battery_logic(s, e)
        self.cfg["batt_start"] = s
        self.cfg["batt_stop"] = e
        ConfigManager.save(self.cfg)

    def update_battery_ui_loop(self):
        info = get_battery_info(self.cached_cycle)
        color = "#2ecc71"
        try:
            if int(info['percent']) < 20: color = "#e74c3c"
        except: pass
        self.lbl_batt_percent.configure(text=f"{info['percent']}%", text_color=color)
        self.lbl_batt_details.configure(text=f"{info['status']} | {info['health']} | {info['cycle']}")
        self.after(5000, self.update_battery_ui_loop)

    def check_updates(self):
        if not GITHUB_USER: return
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                latest = r.json()["tag_name"]
                if latest != CURRENT_VERSION:
                    if ctypes.windll.user32.MessageBoxW(0, f"{self.txt['msg_newvers']}\nIndirmek ister misiniz?", "Update", 4) == 6:
                        webbrowser.open(r.json()["html_url"])
                else:
                    ctypes.windll.user32.MessageBoxW(0, self.txt['msg_uptodate'], "Info", 0x40)
        except: pass

    def toggle_hotkeys(self):
        state = self.switch_hotkey.get()
        self.hotkeys_enabled = bool(state)
        self.cfg["hotkeys"] = self.hotkeys_enabled
        ConfigManager.save(self.cfg)
        self.setup_hotkeys()

    def toggle_autostart(self):
        state = self.switch_auto.get()
        self.autostart_enabled = bool(state)
        self.cfg["autostart"] = self.autostart_enabled
        set_autostart_task(self.autostart_enabled)
        ConfigManager.save(self.cfg)

    def toggle_language(self):
        self.lang_code = "EN" if self.lang_code == "TR" else "TR"
        self.txt = LANGUAGES[self.lang_code]
        self.cfg["lang"] = self.lang_code
        ConfigManager.save(self.cfg)
        self.setup_ui() 

    def persistence_loop(self):
        while self.running:
            if self.current_val != 0x80: write_ec(FAN_REG, self.current_val)
            time.sleep(2.0)

    # --- TRAY MANTIĞI DÜZELTİLDİ ---
    def hide_window(self):
        self.withdraw()
        # İkonu ayrı thread'de oluşturma mantığı sağlamlaştırıldı
        if self.tray_icon is None:
            threading.Thread(target=self.start_tray, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        # İkonu durdurup yok et ki sonra tekrar oluşturabilelim
        if self.tray_icon: 
            self.tray_icon.stop()
            self.tray_icon = None

    def quit_app(self, icon=None, item=None):
        self.running = False
        write_ec(FAN_REG, 0x80)
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit()

    def start_tray(self):
        try:
            icon_img = create_image(self.cfg.get("color", "#2ecc71"))
            menu = (item(self.txt["tray_open"], self.show_window, default=True), item(self.txt["tray_exit"], self.quit_app))
            self.tray_icon = pystray.Icon("ThinkPadUltFinal", icon_img, "Command Center", menu)
            self.tray_icon.run()
        except:
            # Hata olursa pencereyi geri getir
            self.deiconify()

    def dashboard_loop(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage('C://').percent
                self.bar_cpu.set(cpu / 100)
                self.lbl_cpu_val.configure(text=f"%{cpu}")
                self.bar_ram.set(ram / 100)
                self.lbl_ram_val.configure(text=f"%{ram}")
                self.bar_disk.set(disk / 100)
                self.lbl_disk_val.configure(text=f"%{disk}")
            except: pass
            time.sleep(1)

if __name__ == "__main__":
    app = FanApp()
    app.mainloop()