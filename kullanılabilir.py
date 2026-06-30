import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import uuid
import re
import sqlite3
import threading
import calendar
import shutil
import logging
import sys
import traceback
from veritabani import VeritabaniYoneticisi
from pdf_motoru import PDFYoneticisi
from araclar import VeriAraclari
from excel_motoru import ExcelMotoru
from sistem_motoru import SistemMotoru
from alt_pencereler import AltPencerelerMixin
from guncelleyici import GuncellemeMotoru
from sabitler import MEVCUT_VERSIYON, UI_FONT, THEME, GITHUB_VERSION_URL, GITHUB_RELEASE_URL

# Yüksek çözünürlüklü (High DPI) ekranlarda bulanıklığı ve boyut kaymasını önler
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except: pass

from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm

try:
    from tkcalendar import Calendar, DateEntry
    TKCALENDAR_VAR = True
except ImportError:
    TKCALENDAR_VAR = False

# --- DOSYA YOLLARI VE VERİTABANI (SİSTEM MOTORU İLE) ---

YOLLAR = SistemMotoru.klasorleri_ve_yollari_hazirla()

VERI_DOSYASI_DB = YOLLAR["DB"]
AYARLAR_DOSYASI = YOLLAR["AYARLAR"]
YEDEK_KLASORU_VARSAYILAN = YOLLAR["YEDEK"]
PDF_KLASORU_VARSAYILAN = YOLLAR["PDF"]
MEB_LOGO_KLASORU = YOLLAR["MEB_LOGO"]
OKUL_LOGO_KLASORU = YOLLAR["OKUL_LOGO"]
GUVENLI_KLASOR = YOLLAR["ANA"]

try: PROGRAM_KLASORU = os.path.dirname(os.path.abspath(__file__))
except: PROGRAM_KLASORU = os.getcwd()

# UI Font Ayarı
UI_FONT = "Segoe UI"

# --- LOGLAMA VE HATA YAKALAMA SİSTEMİ ---
LOG_DOSYASI = YOLLAR.get("LOG", os.path.join(GUVENLI_KLASOR, "sistem_hatalari.log"))

logging.basicConfig(
    filename=LOG_DOSYASI,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' # Türkçe karakterlerin loglarda bozulmaması için
)

def global_hata_yakalayici(exc_type, exc_value, exc_traceback):
    """Programın herhangi bir yerinde oluşan ve yakalanmayan hataları hapseder."""
    hata_detayi = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"BEKLENMEYEN SİSTEM HATASI:\n{hata_detayi}\n{'-'*50}")
    
    try:
        from tkinter import messagebox
        mesaj = (
            "Program çalışırken beklenmeyen bir hata oluştu.\n\n"
            f"Hata detayları güvenli bir şekilde log dosyasına kaydedildi:\n{LOG_DOSYASI}\n\n"
            "İşleminize devam edebilirsiniz ancak sorun tekrarlarsa bu log dosyasını geliştiriciye iletin."
        )
        messagebox.showerror("Sistem Hatası Yakalandı", mesaj)
    except:
        pass

# Dikkat: Bu atama işlemi fonksiyon tanımlandıktan SONRA yapılmalıdır!
sys.excepthook = global_hata_yakalayici


try: PROGRAM_KLASORU = os.path.dirname(os.path.abspath(__file__))
except: PROGRAM_KLASORU = os.getcwd()

# UI Font Ayarı
UI_FONT = "Segoe UI"

class ToolTip(object):
    """Arayüz nesneleri için üzerine gelince açılan ipucu baloncukları oluşturur."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # 0.5 saniye fare üzerinde beklerse açılır

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#1E293B", foreground="#F8FAFC", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=5, ipady=3)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class YoklamaUygulamasi(AltPencerelerMixin):
    def __init__(self, root):
        self.root = root
        self.root.report_callback_exception = global_hata_yakalayici
        self.root.withdraw() 
        self.root.title("Öğrenci Devamsızlık Sistemi - Premium Yönetim Paneli")
        self.root.protocol("WM_DELETE_WINDOW", self.programdan_cik)

        # --- İKON (TÜY SİLİCİ) EKLENTİSİ ---
        try:
            import sys
            # PyInstaller ile .exe yapıldığında ikonun kaybolmasını önleyen özel yol bulucu
            if hasattr(sys, '_MEIPASS'):
                ikon_yolu = os.path.join(sys._MEIPASS, "logo.ico")
            else:
                ikon_yolu = os.path.join(PROGRAM_KLASORU, "logo.ico")
                
            # default parametresi sayesinde Ayarlar, Raporlar gibi Toplevel tüm alt pencerelerden de tüy silinir
            self.root.iconbitmap(default=ikon_yolu) 
        except:
            pass # İkon dosyası bulunamazsa program çökmek yerine sessizce devam eder

        # --- EKSİK OLAN HAFIZA LİSTELERİ (Her şeyden önce tanımlanmalı) ---
        self.ogrenci_listesi = []
        self.devamsizlik_listesi = []
        self.gecici_devamsizliklar = []
        self.secili_ogrenci = None
        self.ayarlar = {}
        self.hovered_row = None  
        self.devamsizlik_onbellek = {}
        self.arama_timer = None 
        self.yukleme_timer = None
        
        # --- PDF İÇİN TÜRKÇE FONT TANIMLAMASI ---
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('ArialTR', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('ArialTR-Bold', 'arialbd.ttf'))
            self.pdf_font = 'ArialTR'
            self.pdf_font_bold = 'ArialTR-Bold'
        except:
            self.pdf_font = 'Helvetica'
            self.pdf_font_bold = 'Helvetica-Bold'

        self.is_dark_mode = False
        self.tema_bg_main = []; self.tema_bg_card = []
        self.tema_fg_main = []; self.tema_fg_sub = []
        self.tema_borders = [] 

        # ... (Font ve diğer tanımlamalar) ...

        # Yeni veritabanı yöneticimizi başlatıyoruz
        self.db = VeritabaniYoneticisi(VERI_DOSYASI_DB)
        self.ayarlari_yukle()
        
        # 1. Verileri RAM'e çek
        self.verileri_yukle()
        
        # 2. Arayüzü çiz
        self.arayuzu_olustur()
        
        # 3. Temayı uygula
        self.temayi_uygula() 
        
        # 4. Listeleri doldur
        self.sube_listesini_guncelle()
        self.ogrenci_tablosunu_doldur()
        
        # 5. Yedekleme zamanlayıcısını kur
        self.zamanlanmis_yedek_kontrolu()
        
        # 6. Splash ekranı başlat
        self.goster_splash()

        # 7. Arka planda sessizce yeni güncelleme var mı diye kontrol et
        GuncellemeMotoru.kontrol_et(MEVCUT_VERSIYON, self.root)

    def programdan_cik(self):
        # Kapanmadan hemen önce pencerenin durumunu ve koordinatlarını kaydet
        if self.root.state() == 'zoomed':
            self.ayarlar["pencere_durumu"] = "zoomed"
        else:
            self.ayarlar["pencere_durumu"] = "normal"
            self.ayarlar["pencere_boyutu"] = self.root.geometry()
            
        self.ayarlari_kaydet() # Ayarları dosyaya yaz
        self.verileri_kaydet()
        self.root.destroy()
    # --- SPLASH EKRAN VE ONBOARDING ---
    def goster_splash(self):
        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True)
        w, h = 450, 250
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg="#0F172A", highlightbackground="#38BB94", highlightthickness=2)
        
        tk.Label(splash, text="⛭ OTO-YOKLAMA", font=(UI_FONT, 28, "bold"), fg="#38BB94", bg="#0F172A").pack(expand=True, pady=(40,0))
        tk.Label(splash, text="Sistem Altyapısı Hazırlanıyor...", font=(UI_FONT, 11), fg="#94A3B8", bg="#0F172A").pack(pady=20)
        
        splash.update() # Ana döngüyü beklemeden ekranı anında çiz
        self.root.after(1500, lambda: self.kapat_splash(splash))

    def kapat_splash(self, splash):
        splash.destroy()
        self.root.deiconify() 
        
        # --- PENCERE BOYUTUNU VE TABLOLARI SAHNEYE ÇIKARKEN YÜKLE ---
        pencere_durumu = self.ayarlar.get("pencere_durumu", "zoomed")
        pencere_boyutu = self.ayarlar.get("pencere_boyutu", "1200x700+100+100")
        
        if pencere_durumu == "zoomed":
            try: self.root.state('zoomed')
            except: self.root.attributes('-zoomed', True)
        else:
            self.root.state('normal')
            self.root.geometry(pencere_boyutu)
            
        # Tabloları burada dolduruyoruz (Hatalı hizalama kodu silindi)
        self.sube_listesini_guncelle()
        self.ogrenci_tablosunu_doldur()
        
        if self.ayarlar.get("ilk_kullanim", True):
            self.bildirim_goster("Sisteme Hoş Geldiniz! Önce Ayarlar menüsünden PDF kayıt yerini seçiniz.", "bilgi")
            self.ayarlar["ilk_kullanim"] = False
            self.ayarlari_kaydet()

    # --- OTOMATİK ÇİZGİ (SASH) HİZALAMA MOTORU ---
    def pencereleri_hizala(self):
        self.root.update_idletasks()
        gen_w = self.root.winfo_width()
        if gen_w > 100:
            try:
                # Çizgiyi üstteki beyaz arama kutusunun tam bittiği yere kilitler
                sol_w = self.filtre_card.winfo_reqwidth() + 10 
                self.paned.sashpos(0, sol_w)
            except: pass
            
            if hasattr(self, 'paned_icerik') and self.paned_icerik.winfo_exists():
                sag_w = self.sag_panel.winfo_width()
                takvim_w = int(sag_w * 0.52) 
                try: self.paned_icerik.sashpos(0, takvim_w)
                except: pass
                
# --- ANİMASYONLU BİLDİRİM (ÜST ORTA KONUM) ---
    def bildirim_goster(self, mesaj, tur="bilgi"):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.attributes("-alpha", 0.0) 
        
        bg_renk = "#10B981" if tur == "bilgi" else "#EF4444"
        toast.configure(bg=bg_renk, highlightbackground="#065F46", highlightthickness=1)
        
        lbl = tk.Label(toast, text=mesaj, fg="white", bg=bg_renk, font=(UI_FONT, 10, "bold"), padx=25, pady=12)
        lbl.pack()
        
        toast.update_idletasks()
        t_width = toast.winfo_width()
        
        # GÜNCELLEME: Konum "Üst Orta" (Top-Center) olarak ayarlandı.
        # Ekran genişliğinin tam ortasından bildirimin kendi genişliğinin yarısını çıkararak merkezliyoruz.
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (t_width // 2)
        target_y = self.root.winfo_y() + 60 # Üst menünün ortasındaki o boş hizaya denk gelir
        start_y = target_y - 40 
        
        toast.geometry(f"+{x}+{start_y}")
        
        def slide_in(current_y, alpha):
            if current_y < target_y:
                toast.geometry(f"+{x}+{current_y}")
                toast.attributes("-alpha", alpha)
                self.root.after(15, slide_in, current_y + 4, min(alpha + 0.1, 0.95))
            else:
                self.root.after(4000, fade_out)

        def fade_out():
            alpha = toast.attributes("-alpha")
            if alpha > 0:
                toast.attributes("-alpha", alpha - 0.05)
                self.root.after(30, fade_out)
            else:
                toast.destroy()
        
        slide_in(start_y, 0.0)

    # --- TEMA MANTIĞI VE YUMUŞAK ÇERÇEVELER ---
    def kayit_ekle(self, widget, tip):
        if type(widget) is list:
            for w in widget: self.kayit_ekle(w, tip)
        else:
            if tip == "bg_main": self.tema_bg_main.append(widget)
            elif tip == "bg_card": self.tema_bg_card.append(widget)
            elif tip == "fg_main": self.tema_fg_main.append(widget)
            elif tip == "fg_sub": self.tema_fg_sub.append(widget)
            elif tip == "border": self.tema_borders.append(widget)

    def temayi_uygula(self):
        if self.is_dark_mode:
            bg_main = "#0F172A"; bg_card = "#1E293B"; fg_main = "#F8FAFC"; fg_sub = "#94A3B8"
            border_color = "#334155" 
            tree_bg = "#1E293B"; tree_fg = "#F8FAFC"; tree_sel = "#38BB94"
            if hasattr(self, 'btn_gece'): self.btn_gece.config(text="☀️ Gündüz Modu", bg="#334155", fg="#FDE047")
        else:
            bg_main = "#F1F5F9"; bg_card = "#FFFFFF"; fg_main = "#1E293B"; fg_sub = "#64748B"
            border_color = "#CBD5E1" 
            tree_bg = "#FFFFFF"; tree_fg = "#334155"; tree_sel = "#38BB94"
            if hasattr(self, 'btn_gece'): self.btn_gece.config(text="🌙 Gece Modu", bg="#E2E8F0", fg="#1E293B")

        self.root.configure(bg=bg_main)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg, borderwidth=0, rowheight=32, font=(UI_FONT, 10))
        style.map("Treeview", background=[("selected", tree_sel)], foreground=[("selected", "#FFFFFF")])
        style.configure("Treeview.Heading", background=bg_main, foreground=fg_main, font=(UI_FONT, 10, "bold"), relief="flat", padding=6)
        style.configure("TCombobox", relief="flat", background=bg_card, foreground=fg_main, bordercolor=border_color)

        for frame in self.tema_bg_main:
            try: frame.configure(bg=bg_main)
            except: pass
        for card in self.tema_bg_card:
            try: card.configure(bg=bg_card, highlightbackground=border_color)
            except: pass
        for lbl in self.tema_fg_main:
            try: lbl.configure(bg=bg_card, fg=fg_main)
            except: pass
        for lbl in self.tema_fg_sub:
            try: lbl.configure(bg=bg_card, fg=fg_sub)
            except: pass
        for border in self.tema_borders:
            try: border.configure(bg=border_color)
            except: pass
            
        if hasattr(self, 'tree_tum_liste'):
            if self.is_dark_mode: 
                self.tree_tum_liste.tag_configure('kirmizi', background='#7F1D1D', foreground='#FEF2F2')
                self.tree_tum_liste.tag_configure('hover', background='#334155')
            else: 
                self.tree_tum_liste.tag_configure('kirmizi', background='#FEE2E2', foreground='#991B1B')
                self.tree_tum_liste.tag_configure('hover', background='#E2E8F0')

        if self.secili_ogrenci: self.detay_paneli_ciz()

    def toggle_gece_modu(self):
        self.is_dark_mode = not self.is_dark_mode
        self.temayi_uygula()

    def style_button(self, btn, bg_color, fg_color, hover_color, font_size=10):
        btn.config(bg=bg_color, fg=fg_color, activebackground=hover_color, activeforeground=fg_color, relief="flat", bd=0, cursor="hand2", font=(UI_FONT, font_size, "bold"))
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color) if btn["state"] != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color) if btn["state"] != "disabled" else None)

    # --- VERİTABANI İŞLEMLERİ VE YEDEKLEME ---
    def verileri_kaydet(self):
        basarili, hata = self.db.kaydet(self.ogrenci_listesi, self.devamsizlik_listesi)
        if not basarili:
            messagebox.showerror("Kayıt Hatası", f"Veritabanı kaydedilemedi:\n{hata}")
        else:
            self.onbellek_guncelle() # Veri her değiştiğinde önbelleği gizlice tazele

    def verileri_yukle(self):
        self.ogrenci_listesi, self.devamsizlik_listesi = self.db.yukle()
        self.onbellek_guncelle()
        
        # --- PERSONEL VERİTABANI BAĞLANTISI (GRUP DESTEKLİ) ---
        try:
            self.db.cursor.execute("CREATE TABLE IF NOT EXISTS personel (ad_soyad TEXT, brans TEXT, gorev TEXT, grup TEXT)")
            # Eski sürümden kalan tabloya 'grup' sütunu ekleme zırhı
            self.db.cursor.execute("PRAGMA table_info(personel)")
            sutunlar = [col[1] for col in self.db.cursor.fetchall()]
            if 'grup' not in sutunlar:
                self.db.cursor.execute("ALTER TABLE personel ADD COLUMN grup TEXT DEFAULT 'Diğer Personel'")
            self.db.conn.commit()
            
            self.db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
            self.personel_listesi = [{'ad': r[0], 'brans': r[1], 'gorev': r[2], 'grup': r[3], 'haric': False} for r in self.db.cursor.fetchall()]
        except Exception as e:
            self.personel_listesi = []
            print(f"Personel yükleme hatası: {e}")

    def onbellek_guncelle(self):
        """100 Milyon işlemi 50 Bine düşüren Hızlı Gruplama (Dictionary Mapping) Motoru"""
        self.devamsizlik_onbellek.clear()
        
        # 1. Bütün devamsızlıkları öğrenci numarasına göre RAM'de "klasörle" (Tek seferlik işlem)
        gruplu_devamsizlik = {}
        for dev in self.devamsizlik_listesi:
            no = str(dev['no']).strip()
            if no not in gruplu_devamsizlik:
                gruplu_devamsizlik[no] = []
            gruplu_devamsizlik[no].append(dev)

        # 2. Herkesin hesabını sadece kendi "kısa listesiyle" yap
        for ogr in self.ogrenci_listesi:
            ogr_no = str(ogr['no']).strip()
            ogr_devleri = gruplu_devamsizlik.get(ogr_no, [])
            ozsz, ozrl = VeriAraclari.hesapla_devamsizlik(ogr_no, ogr_devleri, [])
            self.devamsizlik_onbellek[ogr_no] = (ozsz, ozrl)
            
    def logo_kontrol_et(self):
        # 1. MEB Logo Kontrolü
        meb_logo = self.ayarlar.get("meb_logosu", "")
        if not meb_logo or not os.path.exists(meb_logo):
            bulundu = False
            for f in os.listdir(MEB_LOGO_KLASORU):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.ayarlar["meb_logosu"] = os.path.join(MEB_LOGO_KLASORU, f)
                    bulundu = True; break
            if not bulundu:
                self.root.after(3000, lambda: self.bildirim_goster("MEB Logosu bulunamadı! Ayarlar'dan yükleyin.", "hata"))

        # 2. Okul Logo Kontrolü
        okul_logo = self.ayarlar.get("okul_logosu", "")
        if not okul_logo or not os.path.exists(okul_logo):
            bulundu = False
            for f in os.listdir(OKUL_LOGO_KLASORU):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.ayarlar["okul_logosu"] = os.path.join(OKUL_LOGO_KLASORU, f)
                    bulundu = True; break
            if not bulundu:
                self.root.after(4500, lambda: self.bildirim_goster("Okul Logosu bulunamadı! Ayarlar'dan yükleyin.", "hata"))
        self.ayarlari_kaydet()

    def veritabani_sifirla(self):
        cevap = messagebox.askyesno("Sıfırla", "Tüm veriler kalıcı olarak silinecek! Emin misiniz?")
        if cevap:
            self.ogrenci_listesi.clear(); self.devamsizlik_listesi.clear(); self.gecici_devamsizliklar.clear()
            self.secili_ogrenci = None
            self.verileri_kaydet(); self.sube_listesini_guncelle(); self.ogrenci_tablosunu_doldur()
            self.detay_paneli_ciz()
            self.bildirim_goster("Veritabanı tamamen sıfırlandı.", "bilgi")
            if hasattr(self, 'ayar_win'): self.ayar_win.destroy()

    def pdf_klasor_sec(self):
        yol = filedialog.askdirectory(title="Kayıt Klasörü Seçin")
        if yol:
            self.ayarlar["pdf_kayit_klasoru"] = yol; self.ayarlari_kaydet()
            return yol
        return None

    # --- HESAPLAMA VE VERİ ARAÇLARI KÖPRÜSÜ ---
    def temiz_sure(self, sure_degeri): return VeriAraclari.temiz_sure(sure_degeri)
    def kisa_sube_adi(self, sube_str): return VeriAraclari.kisa_sube_adi(sube_str)
    def tarih_formatla(self, tarih_str): return VeriAraclari.tarih_formatla(tarih_str)
    def excel_tarih_cevir(self, excel_tarih): return VeriAraclari.excel_tarih_cevir(excel_tarih)
    def _parse_tarih(self, t_str): return VeriAraclari.parse_tarih(t_str)
    def tr_upper(self, metin): return VeriAraclari.tr_upper(metin)
    
    def hesapla_devamsizlik(self, ogr_no): 
        # Matematiksel hesaplamayı devamsızlık listelerini de göndererek araca devrediyoruz
        return VeriAraclari.hesapla_devamsizlik(ogr_no, self.devamsizlik_listesi, self.gecici_devamsizliklar)

    def filtre_temizle(self):
        # Yeni tek parça arama kutusuna göre temizleme işlemi
        if hasattr(self, 'ent_arama'):
            self.ent_arama.delete(0, tk.END)
            self.ent_arama.insert(0, "Numara veya Ad Soyad")
            self.ent_arama.config(fg="gray")
            self.combo_arama_sube.current(0)
            self.ogrenci_tablosunu_doldur()
            self.root.focus_set() # Seçimi kutudan çıkarır, yazıyı tekrar grileştirir

    def tr_karakter_duzelt(self, metin):
        if self.pdf_font == 'Helvetica':
            degisim = {'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ç': 'c', 'Ç': 'C', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
            for a, b in degisim.items(): metin = metin.replace(a, b)
        return metin
    
    # --- TREEVIEW HOVER VE SÜTUN AYARLARI ---
    def sutun_genisliklerini_ayarla(self, tree):
        self.root.update_idletasks()
        
        # Treeview'in net genişliğini üstteki beyaz kutuya kilitliyoruz. Kaydırma çubuğu için 25px çıkarıyoruz.
        try: net_genislik = self.filtre_card.winfo_reqwidth() - 25
        except: net_genislik = 400 
            
        # Boşluğu sütun sayısına oranlayarak bölüyoruz (Senin İstediğin Özellik)
        w_no = int(net_genislik * 0.12)
        w_ad = int(net_genislik * 0.40)
        w_sube = int(net_genislik * 0.16)
        w_ozsz = int(net_genislik * 0.16)
        w_ozrl = int(net_genislik * 0.16)

        # Yeni sıraya göre genişlik atamaları
        tree.column("Sube", width=w_sube, minwidth=w_sube, stretch=True, anchor=tk.W)
        tree.column("No", width=w_no, minwidth=w_no, stretch=True, anchor=tk.W)
        tree.column("Ad", width=w_ad, minwidth=w_ad, stretch=True, anchor=tk.W)
        tree.column("Ozursuz", width=w_ozsz, minwidth=w_ozsz, stretch=True, anchor=tk.W)
        tree.column("Ozurlu", width=w_ozrl, minwidth=w_ozrl, stretch=True, anchor=tk.W)

    def tree_on_motion(self, event):
        item = self.tree_tum_liste.identify_row(event.y)
        if item != self.hovered_row:
            if self.hovered_row and self.tree_tum_liste.exists(self.hovered_row):
                self.tree_tum_liste.item(self.hovered_row, tags=self.hover_orjinal_tag)
            
            if item:
                self.hover_orjinal_tag = self.tree_tum_liste.item(item, "tags")
                yeni_tag = tuple(t for t in self.hover_orjinal_tag if t != "hover") + ("hover",)
                self.tree_tum_liste.item(item, tags=yeni_tag)
                
            self.hovered_row = item

    def tree_on_leave(self, event):
        if self.hovered_row and self.tree_tum_liste.exists(self.hovered_row):
            self.tree_tum_liste.item(self.hovered_row, tags=self.hover_orjinal_tag)
        self.hovered_row = None

# --- YENİ RAPORLAR PENCERESİ (DİNAMİK BOYUTLANDIRMA) ---
    
    
            
    # --- ANA ARAYÜZ ---
    # --- ANA ARAYÜZ ---
    def arayuzu_olustur(self):
        # 1. SEKME MOTORUNU (NOTEBOOK) OLUŞTUR VE ANA PENCEREYE YAPIŞTIR
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 2. İKİ FARKLI SAYFA (FRAME) YARAT
        bg_main_color = "#0F172A" if self.is_dark_mode else "#F1F5F9"
        self.sekme_izin = tk.Frame(self.notebook, bg=bg_main_color)
        self.sekme_teblig = tk.Frame(self.notebook, bg=bg_main_color)

        # 3. SAYFALARI DEFTERE (NOTEBOOK) EKLE
        self.notebook.add(self.sekme_izin, text="📄 İzin Dilekçesi")
        self.notebook.add(self.sekme_teblig, text="🖋️ Yazı Tebliği")

        # 4. ESKİ "ANA" ÇERÇEVEYİ ARTIK "ROOT" YERİNE "SEKME_IZIN" İÇİNE HAPSEDİYORUZ
        ana = tk.Frame(self.sekme_izin, padx=25, pady=25)
        ana.pack(fill=tk.BOTH, expand=True)
        self.kayit_ekle(ana, "bg_main")

        top_bar = tk.Frame(ana, highlightthickness=1, padx=20, pady=15)
        top_bar.pack(fill=tk.X, pady=(0, 15))
        self.kayit_ekle(top_bar, "bg_card")

        tk.Label(top_bar, text="YOKLAMA YÖNETİM PANELİ", font=(UI_FONT, 15, "bold"), fg="#38BB94").pack(side=tk.LEFT, padx=(0,30))
        self.kayit_ekle(top_bar.winfo_children()[0], "bg_card")

        # Yardım butonu (En sağda durması için önce pack ediliyor)
        btn_yardim = tk.Button(top_bar, text="❓ Yardım", command=self.yardim_penceresi_ac, padx=15, pady=6)
        btn_yardim.pack(side=tk.RIGHT, padx=5); self.style_button(btn_yardim, "#F59E0B", "#FFFFFF", "#D97706", font_size=10)

        # Ayarlar butonu (Yardım butonunun solunda kalacak)
        btn_ayar = tk.Button(top_bar, text="⚙️ Ayarlar", command=self.ayarlar_penceresi_ac, padx=15, pady=6)
        btn_ayar.pack(side=tk.RIGHT, padx=5); self.style_button(btn_ayar, "#475569", "#FFFFFF", "#64748B", font_size=10)

        self.btn_gece = tk.Button(top_bar, text="Gece Modu", command=self.toggle_gece_modu, padx=15, pady=6)
        self.btn_gece.pack(side=tk.RIGHT, padx=5); self.style_button(self.btn_gece, "#E2E8F0", "#1E293B", "#CBD5E1", font_size=10)

        btn_rapor = tk.Button(top_bar, text="📄 Raporlar", command=self.rapor_penceresi_ac, padx=15, pady=6)
        btn_rapor.pack(side=tk.RIGHT, padx=5); self.style_button(btn_rapor, "#4F46E5", "#FFFFFF", "#6366F1", font_size=10)

        btn_dev = tk.Button(top_bar, text="Devamsızlık Yükle", command=self.devamsizlik_yukle_thread, padx=15, pady=6)
        btn_dev.pack(side=tk.RIGHT, padx=5); self.style_button(btn_dev, "#2563EB", "#FFFFFF", "#3B82F6", font_size=10)

        btn_ogr = tk.Button(top_bar, text="Öğrenci Yükle", command=self.ogrenci_yukle_thread, padx=15, pady=6)
        btn_ogr.pack(side=tk.RIGHT, padx=5); self.style_button(btn_ogr, "#059669", "#FFFFFF", "#10B981", font_size=10)

        self.paned = ttk.PanedWindow(ana, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --- SOL PANEL ---
       # --- SOL PANEL ---
        sol_panel = tk.Frame(self.paned)
        # 1. Paneli BÜYÜMEZ KATI YAPIYA (weight=0) alıyoruz.
        self.paned.add(sol_panel, weight=0) 
        self.kayit_ekle(sol_panel, "bg_main")

        # 2. filtre_card'ı self.filtre_card yapıyoruz ki diğer fonksiyonlar ölçüsünü okuyabilsin
        self.filtre_card = tk.Frame(sol_panel, highlightthickness=1, padx=10, pady=15)
        self.filtre_card.pack(fill=tk.X, pady=(0, 10), padx=5); self.kayit_ekle(self.filtre_card, "bg_card")
        
        # 3. Arama çubuğunu MERKEZLİYORUZ (YENİ TEK PARÇA ARAMA KUTUSU)
        arama_grid = tk.Frame(self.filtre_card)
        arama_grid.pack(anchor=tk.CENTER)
        self.kayit_ekle(arama_grid, "bg_card")

        l_ara = tk.Label(arama_grid, text="Ara:", font=(UI_FONT, 10, "bold"))
        l_ara.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.kayit_ekle(l_ara, "bg_card"); self.kayit_ekle(l_ara, "fg_main")

        f_ara = tk.Frame(arama_grid, padx=1, pady=1)
        f_ara.grid(row=0, column=1, padx=(0,15), pady=5)
        self.kayit_ekle(f_ara, "border")
        
        self.ent_arama = tk.Entry(f_ara, width=28, font=(UI_FONT, 10), relief="flat", bd=0)
        self.ent_arama.pack(fill=tk.BOTH, expand=True, ipadx=5, ipady=4)
        self.kayit_ekle(self.ent_arama, "bg_card")

        # Placeholder (Yer Tutucu) Sistemi
        p_text = "Numara veya Ad Soyad"
        self.ent_arama.insert(0, p_text)
        self.ent_arama.config(fg="gray")

        def on_focus_in(e):
            if self.ent_arama.get() == p_text:
                self.ent_arama.delete(0, tk.END)
                self.ent_arama.config(fg="#F8FAFC" if self.is_dark_mode else "#0F172A")
                
        def on_focus_out(e):
            if not self.ent_arama.get().strip():
                self.ent_arama.delete(0, tk.END)
                self.ent_arama.insert(0, p_text)
                self.ent_arama.config(fg="gray")
                self.ogrenci_tablosunu_doldur()
                
        def on_key_release(e):
            p_text = "Numara veya Ad Soyad"
            if self.ent_arama.get() != p_text:
                if hasattr(self, 'arama_timer') and self.arama_timer is not None:
                    self.root.after_cancel(self.arama_timer)
                self.arama_timer = self.root.after(300, self.ogrenci_tablosunu_doldur)

        self.ent_arama.bind("<FocusIn>", on_focus_in)
        self.ent_arama.bind("<FocusOut>", on_focus_out)
        self.ent_arama.bind("<KeyRelease>", on_key_release)

        # --- ŞUBE VE TEMİZLE BUTONLARI (Silinen Kısım 1) ---
        l_sube = tk.Label(arama_grid, text="Şube:", font=(UI_FONT, 10, "bold"))
        l_sube.grid(row=0, column=2, padx=(0,5), pady=5, sticky=tk.W)
        self.kayit_ekle(l_sube, "bg_card"); self.kayit_ekle(l_sube, "fg_main")
        
        sube_cerceve = tk.Frame(arama_grid, padx=1, pady=1)
        sube_cerceve.grid(row=0, column=3, padx=(0,15), pady=5)
        self.kayit_ekle(sube_cerceve, "border")
        
        self.combo_arama_sube = ttk.Combobox(sube_cerceve, values=["Tümü"], state="readonly", width=12, font=(UI_FONT, 10))
        self.combo_arama_sube.pack()
        self.combo_arama_sube.current(0)
        self.combo_arama_sube.bind("<<ComboboxSelected>>", lambda e: self.ogrenci_tablosunu_doldur())

        btn_temizle = tk.Button(arama_grid, text="Temizle", command=self.filtre_temizle, padx=12, pady=3, font=(UI_FONT, 10, "bold"))
        btn_temizle.grid(row=0, column=4, padx=(5,0), pady=5)
        self.style_button(btn_temizle, "#E2E8F0", "#1E293B", "#CBD5E1")

        # --- LİSTE (TREEVIEW) ALANI (Silinen Kısım 2) ---
        list_card = tk.Frame(sol_panel, highlightthickness=1)
        list_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        self.kayit_ekle(list_card, "bg_card"); self.kayit_ekle(list_card, "border")

        vsb = ttk.Scrollbar(list_card, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill='y')

        # Sütun sırası güncellendi
        self.tree_tum_liste = ttk.Treeview(list_card, columns=("Sube", "No", "Ad", "Ozursuz", "Ozurlu"), show="headings", yscrollcommand=vsb.set)
        vsb.config(command=self.tree_tum_liste.yview)

        # Başlıklar yeni sıraya göre eklendi
        self.tree_tum_liste.heading("Sube", text="Sınıf", anchor=tk.W, command=lambda: self.sort_treeview_column("Sube", False))
        self.tree_tum_liste.heading("No", text="No", anchor=tk.W, command=lambda: self.sort_treeview_column("No", False))
        self.tree_tum_liste.heading("Ad", text="Ad Soyad", anchor=tk.W, command=lambda: self.sort_treeview_column("Ad", False))
        self.tree_tum_liste.heading("Ozursuz", text="Özürsüz", anchor=tk.W, command=lambda: self.sort_treeview_column("Ozursuz", False))
        self.tree_tum_liste.heading("Ozurlu", text="Özürlü", anchor=tk.W, command=lambda: self.sort_treeview_column("Ozurlu", False))

        # --- EKSİK OLAN VE LİSTEYİ GÖRÜNÜR YAPAN SATIR ---
        self.tree_tum_liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_tum_liste.bind("<ButtonRelease-1>", self.ogrenci_tek_tiklandi)

        if hasattr(self, 'ogrenci_cift_tiklandi'): self.tree_tum_liste.bind("<Double-1>", self.ogrenci_cift_tiklandi)
        self.tree_tum_liste.bind("<Button-3>", self.sag_tik_goster)
        self.tree_tum_liste.bind("<Motion>", self.tree_on_motion)
        self.tree_tum_liste.bind("<Leave>", self.tree_on_leave)

        # --- SAĞ PANEL - TAKVİM VE ÖNİZLEME (Silinen Kısım 3) ---
        self.sag_panel = tk.Frame(self.paned)
        self.paned.add(self.sag_panel, weight=1)
        self.kayit_ekle(self.sag_panel, "bg_main")

        # --- SAĞ TIK MENÜSÜ ---
        self.sag_tik_menu = tk.Menu(self.root, tearoff=0, font=(UI_FONT, 10))
        self.sag_tik_menu.add_command(label="Numarayı Kopyala", command=self.kopyala_no)
        self.sag_tik_menu.add_command(label="Adı Kopyala", command=self.kopyala_ad)
        self.sag_tik_menu.add_separator() # Araya şık bir ayırıcı çizgi çeker
        self.sag_tik_menu.add_command(label="Öğrenciyi Sil", command=self.ogrenciyi_sil)

        # --- KISAYOL TUŞLARI (YENİ EKLENEN KISIM) ---
        self.root.bind("<Control-f>", lambda e: self.ent_arama.focus_set())
        self.root.bind("<Control-F>", lambda e: self.ent_arama.focus_set())
        self.root.bind("<Delete>", lambda e: self.ogrenciyi_sil() if getattr(self, 'secili_ogrenci', None) else None)
        self.root.bind("<Control-p>", lambda e: self.pdf_ciktisi_al() if getattr(self, 'secili_ogrenci', None) else None)
        self.root.bind("<Control-P>", lambda e: self.pdf_ciktisi_al() if getattr(self, 'secili_ogrenci', None) else None)
        self.root.bind("<Control-s>", lambda e: self.manuel_yedek_al())
        self.root.bind("<Control-S>", lambda e: self.manuel_yedek_al())
        self.teblig_arayuzunu_olustur()

    # --- 2. SEKME: YAZI TEBLİĞİ İŞLEMLERİ ---
      # ÜST PANEL: BUTONLAR
    def teblig_arayuzunu_olustur(self):
        teblig_ana = tk.Frame(self.sekme_teblig, padx=25, pady=25)
        teblig_ana.pack(fill=tk.BOTH, expand=True)
        self.kayit_ekle(teblig_ana, "bg_main")
       
        ust_panel = tk.Frame(teblig_ana, highlightthickness=1, padx=20, pady=15)
        ust_panel.pack(fill=tk.X, pady=(0, 15))
        self.kayit_ekle(ust_panel, "bg_card")

        tk.Label(ust_panel, text="TEBLİĞ OLUŞTURMA MERKEZİ", font=(UI_FONT, 14, "bold"), fg="#4F46E5").pack(side=tk.LEFT)
        self.kayit_ekle(ust_panel.winfo_children()[0], "bg_card")

        # 1. Personel Yönetimi Butonu (En sağa eklendi)
        btn_personel_yonet = tk.Button(ust_panel, text="⚙️ Personel Ekle / Çıkar", command=self.personel_yonetim_penceresi_ac, padx=15, pady=6)
        btn_personel_yonet.pack(side=tk.RIGHT, padx=5)
        self.style_button(btn_personel_yonet, "#475569", "#FFFFFF", "#334155", font_size=10)

        # 2. Excel Yükleme Butonu
        btn_personel_yukle = tk.Button(ust_panel, text="👥 Personel Listesi (Excel) Yükle", command=self.personel_yukle_motoru, padx=15, pady=6)
        btn_personel_yukle.pack(side=tk.RIGHT, padx=5)
        self.style_button(btn_personel_yukle, "#10B981", "#FFFFFF", "#059669", font_size=10)

        # 3. PDF Yükleme Butonu
        btn_pdf_yukle = tk.Button(ust_panel, text="📄 MEB Yazısı (PDF) Yükle", command=self.pdf_yukle_motoru, padx=15, pady=6)
        btn_pdf_yukle.pack(side=tk.RIGHT, padx=5)
        self.style_button(btn_pdf_yukle, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)

        # ORTA BÖLÜM: YAZI BİLGİLERİ (Her iki panelin ortak kullanacağı kısım)
        yazi_panel = tk.Frame(teblig_ana, highlightthickness=1, padx=15, pady=10)
        yazi_panel.pack(fill=tk.X, pady=(0, 15))
        self.kayit_ekle(yazi_panel, "bg_card"); self.kayit_ekle(yazi_panel, "border")
        
        tk.Label(yazi_panel, text="Resmi Yazı Detayları (Ortak Kullanım)", font=(UI_FONT, 11, "bold")).pack(anchor=tk.W, pady=(0,5))
        self.kayit_ekle(yazi_panel.winfo_children()[0], "bg_card"); self.kayit_ekle(yazi_panel.winfo_children()[0], "fg_main")

        ic_yazi = tk.Frame(yazi_panel); ic_yazi.pack(fill=tk.X)
        self.kayit_ekle(ic_yazi, "bg_card")

        def yatay_kutu_ekle(parent, etiket):
            frm = tk.Frame(parent)
            frm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.kayit_ekle(frm, "bg_card")
            lbl = tk.Label(frm, text=etiket, width=6, anchor=tk.W, font=(UI_FONT, 10, "bold"))
            lbl.pack(side=tk.LEFT)
            self.kayit_ekle(lbl, "bg_card"); self.kayit_ekle(lbl, "fg_main")
            ent = tk.Entry(frm, font=(UI_FONT, 10), relief="solid", bd=1)
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0), ipady=2)
            return ent

        self.ent_teblig_sayi = yatay_kutu_ekle(ic_yazi, "Sayı:")
        self.ent_teblig_konu = yatay_kutu_ekle(ic_yazi, "Konu:")
        self.ent_teblig_tarih = yatay_kutu_ekle(ic_yazi, "Tarih:")

        # ================= ALT BÖLÜM: İKİYE BÖLÜNMÜŞ EKRAN =================
        paned_teblig = ttk.PanedWindow(teblig_ana, orient=tk.HORIZONTAL)
        paned_teblig.pack(fill=tk.BOTH, expand=True)

        # ---------------- SOL KISIM: TOPLU İMZA LİSTESİ ----------------
        sol_panel = tk.Frame(paned_teblig, highlightthickness=1, padx=15, pady=15)
        paned_teblig.add(sol_panel, weight=1)
        self.kayit_ekle(sol_panel, "bg_card"); self.kayit_ekle(sol_panel, "border")
        
        tk.Label(sol_panel, text="📑 Toplu İmza Sirküsü", font=(UI_FONT, 12, "bold"), fg="#4F46E5").pack(anchor=tk.W, pady=(0,10))
        self.kayit_ekle(sol_panel.winfo_children()[0], "bg_card")

        # === YENİ NESİL HİBRİT FİLTRE ALANI ===
        filtre_f = tk.Frame(sol_panel); filtre_f.pack(fill=tk.X, pady=(0, 10))
        self.kayit_ekle(filtre_f, "bg_card")
        
        # 1. Akıllı Arama Çubuğu
        f_arama = tk.Frame(filtre_f); f_arama.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.kayit_ekle(f_arama, "bg_card")
        tk.Label(f_arama, text="🔍 Ara:", font=(UI_FONT, 9, "bold")).pack(side=tk.LEFT)
        self.kayit_ekle(f_arama.winfo_children()[0], "bg_card"); self.kayit_ekle(f_arama.winfo_children()[0], "fg_main")
        
        self.ent_arama = tk.Entry(f_arama, font=(UI_FONT, 10), relief="solid", bd=1)
        self.ent_arama.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=3)
        self.ent_arama.bind("<KeyRelease>", lambda e: self.personel_tablosunu_doldur())

        # 2. Excel Tarzı Çoklu Seçim Menüleri
        self.mb_gorev = tk.Menubutton(filtre_f, text="🔻 Görev", relief="raised", font=(UI_FONT, 9), bg="#E2E8F0")
        self.mb_gorev.pack(side=tk.LEFT, padx=2)
        self.menu_gorev = tk.Menu(self.mb_gorev, tearoff=0)
        self.mb_gorev.config(menu=self.menu_gorev)
        
        self.mb_brans = tk.Menubutton(filtre_f, text="🔻 Branş", relief="raised", font=(UI_FONT, 9), bg="#E2E8F0")
        self.mb_brans.pack(side=tk.LEFT, padx=2)
        self.menu_brans = tk.Menu(self.mb_brans, tearoff=0)
        self.mb_brans.config(menu=self.menu_brans)

        # === 4 SÜTUNLU YENİ TABLO (Görev ve Branş Ayrıldı) ===
        tree_scroll_sol = ttk.Scrollbar(sol_panel, orient="vertical")
        tree_scroll_sol.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_personel = ttk.Treeview(sol_panel, columns=("Durum", "Gorev", "Brans", "Ad"), show="headings", yscrollcommand=tree_scroll_sol.set)
        tree_scroll_sol.config(command=self.tree_personel.yview)
        
        self.tree_personel.heading("Durum", text="Seç", anchor=tk.CENTER)
        self.tree_personel.heading("Gorev", text="Görevi", anchor=tk.W)
        self.tree_personel.heading("Brans", text="Branşı", anchor=tk.W)
        self.tree_personel.heading("Ad", text="Adı Soyadı", anchor=tk.W)
        
        self.tree_personel.column("Durum", width=40, anchor=tk.CENTER, stretch=False)
        self.tree_personel.column("Gorev", width=95, anchor=tk.W)
        self.tree_personel.column("Brans", width=95, anchor=tk.W)
        self.tree_personel.column("Ad", width=150, anchor=tk.W)
        self.tree_personel.pack(fill=tk.BOTH, expand=True)

        btn_teblig_olustur = tk.Button(sol_panel, text="📑 Seçili Personel İçin Çıktı Al", command=self.teblig_ciktisi_al, pady=10)
        btn_teblig_olustur.pack(fill=tk.X, pady=(15, 0))
        self.style_button(btn_teblig_olustur, "#10B981", "#FFFFFF", "#059669", font_size=11)

        # ---------------- SAĞ KISIM: BİREYSEL TEBLİĞ-TEBELLÜĞ ----------------
        sag_panel = tk.Frame(paned_teblig, highlightthickness=1, padx=15, pady=15)
        paned_teblig.add(sag_panel, weight=1)
        self.kayit_ekle(sag_panel, "bg_card"); self.kayit_ekle(sag_panel, "border")
        
        tk.Label(sag_panel, text="✉️ Bireysel Tebliğ-Tebellüğ Belgesi", font=(UI_FONT, 12, "bold"), fg="#EA580C").pack(anchor=tk.W, pady=(0,15))
        self.kayit_ekle(sag_panel.winfo_children()[0], "bg_card")

        sag_form = tk.Frame(sag_panel); sag_form.pack(fill=tk.BOTH, expand=True)
        self.kayit_ekle(sag_form, "bg_card")

        def form_kutu(parent, etiket):
            f = tk.Frame(parent); f.pack(fill=tk.X, pady=8)
            self.kayit_ekle(f, "bg_card")
            tk.Label(f, text=etiket, width=15, anchor=tk.W, font=(UI_FONT, 10, "bold")).pack(side=tk.LEFT)
            self.kayit_ekle(f.winfo_children()[0], "bg_card"); self.kayit_ekle(f.winfo_children()[0], "fg_main")
            
            cmb = ttk.Combobox(f, state="readonly", font=(UI_FONT, 10))
            cmb.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            return cmb

        self.combo_teblig_eden = form_kutu(sag_form, "Tebliğ Eden:")
        self.combo_tebellug_eden = form_kutu(sag_form, "Tebellüğ Eden:")
        
        f_yer = tk.Frame(sag_form); f_yer.pack(fill=tk.X, pady=8)
        self.kayit_ekle(f_yer, "bg_card")
        tk.Label(f_yer, text="Tebliğ Edilen Yer:", width=15, anchor=tk.W, font=(UI_FONT, 10, "bold")).pack(side=tk.LEFT)
        self.kayit_ekle(f_yer.winfo_children()[0], "bg_card"); self.kayit_ekle(f_yer.winfo_children()[0], "fg_main")
        self.ent_teblig_yeri = tk.Entry(f_yer, font=(UI_FONT, 10), relief="solid", bd=1)
        self.ent_teblig_yeri.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.ent_teblig_yeri.insert(0, "Okul Müdürlüğü")
        
        info_text = ("📌 Bu bölüm kişiye özel Tebliğ/Tebellüğ makbuzu oluşturur.\n\n"
                     "Çıktı Formatı (Tek PDF):\n"
                     "• 1. Sayfa: Resmi Yazı Özeti (A4 Formatında)\n"
                     "• 2. Sayfa: İki Adet Tebliğ/Tebellüğ Makbuzu (Altlı/Üstlü A5)")
        lbl_info = tk.Label(sag_form, text=info_text, font=(UI_FONT, 9), fg="gray", justify=tk.LEFT, anchor=tk.W)
        lbl_info.pack(fill=tk.X, pady=15)
        self.kayit_ekle(lbl_info, "bg_card")

        btn_bireysel_olustur = tk.Button(sag_panel, text="✉️ Bireysel Tebliğ Çıktısı Al", command=self.bireysel_teblig_ciktisi_al, pady=10)
        btn_bireysel_olustur.pack(fill=tk.X, pady=(15, 0))
        self.style_button(btn_bireysel_olustur, "#EA580C", "#FFFFFF", "#C2410C", font_size=11)

        # Olay tetikleyiciler
        try:
            self.tree_personel.bind("<ButtonRelease-1>", self.personel_secim_toggle)
            self.combo_teblig_brans.bind("<<ComboboxSelected>>", lambda e: self.personel_tablosunu_doldur())
        except: pass

        self.bireysel_teblig_isimleri_guncelle()
        self.dinamik_filtreleri_guncelle()

    # FİLTRE MOTORLARI (GELİŞMİŞ ZEKASIYLA)
    def gruplari_guncelle(self):
        mevcut_gruplar = set([p.get('grup', 'Diğer Personel') for p in getattr(self, 'personel_listesi', [])])
        grup_listesi = ["Tümü"]
        if "İdare" in mevcut_gruplar: grup_listesi.append("İdare")
        if "Öğretmenler" in mevcut_gruplar: grup_listesi.append("Öğretmenler")
        
        digerleri = sorted([g for g in mevcut_gruplar if g not in ["İdare", "Öğretmenler"]])
        grup_listesi.extend(digerleri)
        
        if hasattr(self, 'combo_teblig_grup'):
            eski_secim = self.combo_teblig_grup.get()
            self.combo_teblig_grup['values'] = grup_listesi
            if eski_secim in grup_listesi: self.combo_teblig_grup.set(eski_secim)
            else: self.combo_teblig_grup.current(0)

    def grup_degisti_motoru(self, event=None):
        grup = self.combo_teblig_grup.get()
        if grup == "Öğretmenler":
            self.f_brans.pack(fill=tk.X, pady=5)
            branslar = set([p.get('brans', '-') for p in getattr(self, 'personel_listesi', []) if p.get('grup') == 'Öğretmenler' and p.get('brans', '-') != '-'])
            self.combo_teblig_brans['values'] = ["Tümü"] + sorted(list(branslar))
            self.combo_teblig_brans.current(0)
        else:
            self.f_brans.pack_forget()
        self.teblig_onizleme_guncelle()

    def sag_tik_goster(self, event):
        item = self.tree_tum_liste.identify_row(event.y)
        if item:
            self.tree_tum_liste.selection_set(item)
            self.ogrenci_tek_tiklandi(None) 
            self.sag_tik_menu.post(event.x_root, event.y_root)

    def kopyala_no(self):
        if self.secili_ogrenci:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(self.secili_ogrenci['no']).strip())
            self.bildirim_goster("Numara panoya kopyalandı!", "bilgi")

    def kopyala_ad(self):
        if self.secili_ogrenci:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.secili_ogrenci['ad_soyad'])
            self.bildirim_goster("Ad soyad panoya kopyalandı!", "bilgi")

    def ogrenciyi_sil(self):
        if not self.secili_ogrenci:
            return

        ogr_no = str(self.secili_ogrenci['no']).strip()
        ogr_ad = self.secili_ogrenci['ad_soyad']

        # Güvenlik Zırhı: Yanlışlıkla tıklamalara karşı onay iste
        cevap = messagebox.askyesno(
            "Öğrenciyi Sil",
            f"{ogr_no} numaralı {ogr_ad} sistemden tamamen silinecek!\n\n"
            "Öğrenciye ait tüm devamsızlık kayıtları da kalıcı olarak yok olacak. Bu işlemi onaylıyor musunuz?"
        )

        if cevap:
            # 1. RAM'den (Öğrenci Listesinden) Uçur
            self.ogrenci_listesi = [ogr for ogr in self.ogrenci_listesi if str(ogr['no']).strip() != ogr_no]

            # 2. RAM'den (Devamsızlık Listesinden) Uçur
            self.devamsizlik_listesi = [dev for dev in self.devamsizlik_listesi if str(dev['no']).strip() != ogr_no]

            # 3. Geçici Hafızaları (Önbellek) Temizle
            if ogr_no in self.devamsizlik_onbellek:
                del self.devamsizlik_onbellek[ogr_no]
            
            self.secili_ogrenci = None
            self.secili_ogrenci_devamsizliklari = []
            self.gecici_devamsizliklar = []

            # 4. Diske Kaydet ve Arayüzü Şimşek Gibi Yenile
            self.verileri_kaydet()
            self.sube_listesini_guncelle()
            self.ogrenci_tablosunu_doldur()
            self.detay_paneli_ciz()

            # 5. Başarı Bildirimi
            self.bildirim_goster(f"{ogr_ad} sistemden başarıyla silindi.", "bilgi")


       # --- E-OKUL YILLIK DEVAMSIZLIK TABLOSU VE DETAYLI ÖZET ---
            # --- TABLO SIRALAMA ---
    def sort_treeview_column(self, col, reverse):
        # 1. Sıralama İşlemi
        l = [(self.tree_tum_liste.set(k, col), k) for k in self.tree_tum_liste.get_children('')]
        def clean_numeric(val):
            try: return float(str(val).replace(" Gün", "").strip())
            except: return 0.0

        if col in ("No", "Ozursuz", "Ozurlu"): 
            l.sort(key=lambda t: clean_numeric(t[0]), reverse=reverse)
        elif col == "Sube":
            # YENİ: Şubeleri alfabetik değil, içindeki rakamı (9, 10, 11, 12) bularak sayısal sıralar!
            def sube_key(t):
                import re
                r = re.findall(r'\d+', str(t[0]))
                return (int(r[0]), str(t[0])) if r else (99, str(t[0]))
            l.sort(key=sube_key, reverse=reverse)
        else: 
            l.sort(key=lambda t: self.tr_upper(str(t[0])), reverse=reverse)
            
        for index, (val, k) in enumerate(l): self.tree_tum_liste.move(k, '', index)
        
        # 2. Tıklama yönünü tersine çevir
        self.tree_tum_liste.heading(col, command=lambda: self.sort_treeview_column(col, not reverse))
        
        # 3. Dinamik Ok İşaretleri Sistemi (Sola Yaslı Şekilde)
        basliklar = {
            "Sube": "Sınıf", "No": "No", "Ad": "Ad Soyad",
            "Ozursuz": "Özürsüz", "Ozurlu": "Özürlü"
        }
        
        for c, text in basliklar.items():
            self.tree_tum_liste.heading(c, text=text, anchor=tk.W)
            
        ok = "▼" if reverse else "▲"
        self.tree_tum_liste.heading(col, text=f"{basliklar[col]} {ok}", anchor=tk.W)
        
    def sube_listesini_guncelle(self):
        def sube_anahtari(s):
            rakamlar = re.findall(r'\d+', s)
            # İlk kriter sınıf seviyesi (9,10,11), ikinci kriter şube harfi (A,B,C)
            return (int(rakamlar[0]), s.strip()) if rakamlar else (99, s.strip())
            
        subeler_set = set()
        for ogr in self.ogrenci_listesi:
            if ogr['sube']:
                kisa = self.kisa_sube_adi(ogr['sube'])
                subeler_set.add(kisa)
                
        subeler = sorted(list(subeler_set), key=sube_anahtari)
        if hasattr(self, 'combo_arama_sube'):
            self.combo_arama_sube['values'] = ["Tümü"] + subeler; self.combo_arama_sube.current(0)

    def ogrenci_tablosunu_doldur(self):
        if not hasattr(self, 'tree_tum_liste'): return
        
        # Eğer devam eden bir yükleme animasyonu varsa durdur (Klavyede hızlı yazarken çakışmayı önler)
        if hasattr(self, 'yukleme_timer') and self.yukleme_timer is not None:
            self.root.after_cancel(self.yukleme_timer)
            self.yukleme_timer = None

        self.tree_tum_liste.delete(*self.tree_tum_liste.get_children())
        
        arama_metni = self.ent_arama.get().strip() if hasattr(self, 'ent_arama') else ""
        if arama_metni == "Numara veya Ad Soyad": 
            arama_metni = ""
            
        arama_upper = self.tr_upper(arama_metni)
        f_sube = self.combo_arama_sube.get() if hasattr(self, 'combo_arama_sube') else "Tümü"
        
        # 1. AŞAMA: Ekrana çizim yapmadan eşleşenleri sadece listede topluyoruz
        self.filtrelenmis_ogrenciler = []
        
        for ogr in self.ogrenci_listesi:
            if arama_metni:
                numara_eslesme = arama_metni in str(ogr['no'])
                ad_eslesme = arama_upper in self.tr_upper(ogr['ad_soyad'])
                if not (numara_eslesme or ad_eslesme):
                    continue
            
            kisa_ad = self.kisa_sube_adi(ogr['sube'])
            gosterilen_sube = kisa_ad # Burada da "Şubesi" eki devre dışı bırakıldı
            
            if f_sube != "Tümü" and f_sube != gosterilen_sube: continue
            
            self.filtrelenmis_ogrenciler.append((ogr, gosterilen_sube))

        # 2. AŞAMA: Parçalı yükleme sayacını sıfırla ve motoru başlat
        self.yukleme_indexi = 0
        self.tree_parca_yukle()

    def tree_parca_yukle(self):
        """Treeview'a verileri tek seferde değil, 200'erli paketler halinde akıtır."""
        # Arayüz kapandıysa veya tablo silindiyse işlemi iptal et
        if not hasattr(self, 'tree_tum_liste') or not self.tree_tum_liste.winfo_exists():
            return
            
        bitis = min(self.yukleme_indexi + 200, len(self.filtrelenmis_ogrenciler))
        
        for i in range(self.yukleme_indexi, bitis):
            ogr, gosterilen_sube = self.filtrelenmis_ogrenciler[i]
            
            # Devamsızlıkları veritabanı yerine şimşek hızında önbellekten çekiyoruz!
            ozsz, ozrl = self.devamsizlik_onbellek.get(ogr['no'], (0.0, 0.0))
            tag = "kirmizi" if ozsz >= 10 else ""
            
            ozsz_str = int(ozsz) if ozsz.is_integer() else ozsz
            ozrl_str = int(ozrl) if ozrl.is_integer() else ozrl
            
            # Ekrana basma sırası Şube, No, Ad Soyad olarak güncellendi
            self.tree_tum_liste.insert("", tk.END, values=(gosterilen_sube, ogr['no'], ogr['ad_soyad'], f"{ozsz_str} Gün", f"{ozrl_str} Gün"), tags=(tag,) if tag else ())
            
        self.yukleme_indexi = bitis
        
        if self.yukleme_indexi < len(self.filtrelenmis_ogrenciler):
            # Bilgisayarın ekran kartına 10 milisaniye nefes aldır, sonraki 200 kişiyi yükle
            self.yukleme_timer = self.root.after(10, self.tree_parca_yukle)
        else:
            # Tüm yükleme bittiğinde sütunları hizala ve motoru kapat
            self.sutun_genisliklerini_ayarla(self.tree_tum_liste)
            self.yukleme_timer = None

    # --- SAĞ PANEL (DETAY VE TAKVİM) MANTIĞI ---
    def ogrenci_tek_tiklandi(self, event):
        secim = self.tree_tum_liste.selection()
        if not secim: return
        item = self.tree_tum_liste.item(secim[0])
        # İndeksler yeni sütun sırasına göre uyarlandı
        sube = item['values'][0]
        no = str(item['values'][1]).strip()
        ad = item['values'][2]
        
        if not self.secili_ogrenci or self.secili_ogrenci['no'] != no:
            self.gecici_devamsizliklar = [] 
            
            # --- YENİ ZIRH: Tıklanan öğrencinin listesini 1 kez ayır ---
            self.secili_ogrenci_devamsizliklari = [d for d in self.devamsizlik_listesi if str(d['no']).strip() == no]
            
            for dev in self.secili_ogrenci_devamsizliklari: 
                dev['secili'] = False
                       
        self.secili_ogrenci = {'no': no, 'ad_soyad': ad, 'sube': sube}
        self.detay_paneli_ciz()

    def detay_paneli_ciz(self):
        for widget in self.sag_panel.winfo_children(): widget.destroy()
        
        bg_card = "#1E293B" if self.is_dark_mode else "#FFFFFF"
        fg_main = "#F8FAFC" if self.is_dark_mode else "#1E293B"
        fg_sub = "#94A3B8" if self.is_dark_mode else "#64748B"
        bg_main = "#0F172A" if self.is_dark_mode else "#F1F5F9"
        border_color = "#334155" if self.is_dark_mode else "#CBD5E1"
        
        self.sag_panel.configure(bg=bg_card)

        if not self.secili_ogrenci:
            lbl = tk.Label(self.sag_panel, text="👈 İşlem yapmak için sol taraftaki listeden bir öğrenci seçin.\n(Yıllık Tablo İçin Çift Tıklayın)", font=(UI_FONT, 13), fg=fg_sub, bg=bg_card)
            lbl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            return

        ust_frame = tk.Frame(self.sag_panel, bg=bg_card)
        ust_frame.pack(fill=tk.X, padx=25, pady=(25,10))
        
        isim_lbl = tk.Label(ust_frame, text=f"{self.secili_ogrenci['ad_soyad']} ({self.secili_ogrenci['no']})", font=(UI_FONT, 16, "bold"), fg=fg_main, bg=bg_card)
        isim_lbl.pack(side=tk.LEFT)
        
        ozsz, ozrl = self.devamsizlik_onbellek.get(self.secili_ogrenci['no'], (0.0, 0.0))
        ozet_metin = f"Özürsüz: {ozsz} Gün  |  Özürlü: {ozrl} Gün"
        ozet_lbl = tk.Label(ust_frame, text=ozet_metin, font=(UI_FONT, 12, "bold"), fg="#DC2626" if ozsz>=10 else fg_sub, bg=bg_card)
        ozet_lbl.pack(side=tk.RIGHT)

        self.paned_icerik = ttk.PanedWindow(self.sag_panel, orient=tk.HORIZONTAL)
        self.paned_icerik.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        # --- TAKVİM ALANI (SOL) ---
        takvim_card = tk.Frame(self.paned_icerik, bg=bg_card, highlightbackground=border_color, highlightthickness=1, padx=15, pady=15)
        self.paned_icerik.add(takvim_card, weight=52) 

        # Başlık silindi, navigasyon (önceki/sonraki ay) en üste alındı.
        nav_frame = tk.Frame(takvim_card, bg=bg_card)
        nav_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        
        if not hasattr(self, 'cal_month'):
            self.cal_year = datetime.now().year
            self.cal_month = datetime.now().month
        
        btn_prev = tk.Button(nav_frame, text="< Önceki Ay", command=lambda: self.ay_degistir(-1))
        btn_prev.pack(side=tk.LEFT); self.style_button(btn_prev, "#E2E8F0", "#334155", "#CBD5E1")
        
        # Ay/Yıl yazısı 11 puntodan 13 puntoya çıkarıldı
        self.lbl_ay_yil = tk.Label(nav_frame, text="", font=(UI_FONT, 13, "bold"), bg=bg_card, fg=fg_main, width=15)
        self.lbl_ay_yil.pack(side=tk.LEFT, expand=True)

        btn_next = tk.Button(nav_frame, text="Sonraki Ay >", command=lambda: self.ay_degistir(1))
        btn_next.pack(side=tk.RIGHT); self.style_button(btn_next, "#E2E8F0", "#334155", "#CBD5E1")
        toplu_frame = tk.Frame(takvim_card, bg=bg_card, highlightthickness=1, highlightbackground=border_color, padx=15, pady=15)
        toplu_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        
        self.grid_frame = tk.Frame(takvim_card, bg=bg_card)
        self.grid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tk.Label(toplu_frame, text="Hızlı Seçim", font=(UI_FONT, 10, "bold"), bg=bg_card, fg=fg_sub).pack(anchor=tk.CENTER, pady=(0,10))
        
        btn_f = tk.Frame(toplu_frame, bg=bg_card); btn_f.pack(fill=tk.X)
        btn_container = tk.Frame(btn_f, bg=bg_card); btn_container.pack(anchor=tk.CENTER)
        
        aralik_f = tk.Frame(toplu_frame, bg=bg_card)
        aralik_f.pack(fill=tk.X, pady=(12,0))
        aralik_container = tk.Frame(aralik_f, bg=bg_card); aralik_container.pack(anchor=tk.CENTER)
        
        tk.Label(aralik_container, text="Başlangıç:", font=(UI_FONT, 9, "bold"), bg=bg_card, fg=fg_sub).pack(side=tk.LEFT, padx=(0,5))
        
        if TKCALENDAR_VAR:
            self.cal_bas = DateEntry(aralik_container, width=10, date_pattern='dd/mm/yyyy', locale='tr_TR', font=(UI_FONT, 9))
            self.cal_bas.pack(side=tk.LEFT, padx=2)
            tk.Label(aralik_container, text="-  Bitiş:", font=(UI_FONT, 9, "bold"), bg=bg_card, fg=fg_sub).pack(side=tk.LEFT, padx=5)
            self.cal_bit = DateEntry(aralik_container, width=10, date_pattern='dd/mm/yyyy', locale='tr_TR', font=(UI_FONT, 9))
            self.cal_bit.pack(side=tk.LEFT, padx=2)
        else:
            self.cal_bas_ent = tk.Entry(aralik_container, width=10, font=(UI_FONT, 9), relief="solid", bd=1)
            self.cal_bas_ent.insert(0, (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y"))
            self.cal_bas_ent.pack(side=tk.LEFT, padx=2)
            tk.Label(aralik_container, text="- Bitiş:", font=(UI_FONT, 9, "bold"), bg=bg_card, fg=fg_sub).pack(side=tk.LEFT, padx=5)
            self.cal_bit_ent = tk.Entry(aralik_container, width=10, font=(UI_FONT, 9), relief="solid", bd=1)
            self.cal_bit_ent.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.cal_bit_ent.pack(side=tk.LEFT, padx=2)

        btn_aralik = tk.Button(aralik_container, text="Aralığı Getir", command=lambda: self.toplu_secim_yap("aralik"), padx=8, pady=2)
        btn_aralik.pack(side=tk.LEFT, padx=(10,0)); self.style_button(btn_aralik, "#4F46E5", "#FFFFFF", "#4338CA", font_size=9)

        # --- PDF ÖNİZLEME ALANI (SAĞ) ---
        onizleme_card = tk.Frame(self.paned_icerik, bg=bg_card, highlightbackground=border_color, highlightthickness=1, padx=15, pady=15)
        self.paned_icerik.add(onizleme_card, weight=48) 

        ust_bilgi = tk.Frame(onizleme_card, bg=bg_card)
        ust_bilgi.pack(side=tk.TOP, fill=tk.X, pady=(0,10))
        tk.Label(ust_bilgi, text="PDF Önizleme", font=(UI_FONT, 12, "bold"), bg=bg_card, fg=fg_main).pack(side=tk.LEFT)
        self.lbl_detay_ozet = tk.Label(ust_bilgi, text="Toplam: 0 Gün", font=(UI_FONT, 11, "bold"), fg="#DC2626", bg=bg_card)
        self.lbl_detay_ozet.pack(side=tk.RIGHT)

        self.btn_detay_pdf = tk.Button(onizleme_card, text="📄 PDF ÇIKTISI AL", command=self.pdf_ciktisi_al, pady=15, state=tk.DISABLED)
        self.btn_detay_pdf.pack(side=tk.BOTTOM, fill=tk.X, pady=(15,0))
        self.style_button(self.btn_detay_pdf, "#EA580C", "#FFFFFF", "#F97316", font_size=12)
        ToolTip(self.btn_detay_pdf, "Sağdaki önizleme listesinde bulunan kayıtları kullanarak\nresmi A5 Veli Bilgilendirme Formu oluşturur.") # --- İPUCU ---

        # ... (Biraz aşağıda hızlı seçim butonları var) ...
        
        btn_1ay = tk.Button(btn_container, text="Bu Ay", command=lambda: self.toplu_secim_yap("bu_ay"), padx=10, pady=4)
        btn_1ay.pack(side=tk.LEFT, padx=8); self.style_button(btn_1ay, "#64748B", "#FFFFFF", "#475569", font_size=9)
        ToolTip(btn_1ay, "Takvimde seçili olan aya ait tüm\nözürsüz devamsızlıkları listeler.")

        # --- İPUCU ---
        
        btn_2ay = tk.Button(btn_container, text="Son İki Ay", command=lambda: self.toplu_secim_yap("son_iki_ay"), padx=10, pady=4)
        btn_2ay.pack(side=tk.LEFT, padx=8); self.style_button(btn_2ay, "#64748B", "#FFFFFF", "#475569", font_size=9)
        ToolTip(btn_2ay, "Takvimde seçili olan ay ve bir önceki ayın\ntüm özürsüz devamsızlıklarını listeler.")

        # --- İPUCU ---
        
        btn_tumu = tk.Button(btn_container, text="Tümünü Seç", command=lambda: self.toplu_secim_yap("tumu"), padx=10, pady=4)
        btn_tumu.pack(side=tk.LEFT, padx=8); self.style_button(btn_tumu, "#10B981", "#FFFFFF", "#059669", font_size=9)
        ToolTip(btn_tumu, "Öğrenciye ait geçmişteki tüm\nözürsüz devamsızlıkları listeler.")


        # --- İPUCU ---       # Grid sistemi ile butonları %50-%50 paylaştırdık
        btn_islem = tk.Frame(onizleme_card, bg=bg_card)
        btn_islem.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))
        btn_islem.columnconfigure(0, weight=1)
        btn_islem.columnconfigure(1, weight=1)

        btn_cikar = tk.Button(btn_islem, text="⬅ Çıkar", command=self.detay_onizleme_cikar, pady=5)
        btn_cikar.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.style_button(btn_cikar, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)

        btn_temizle_oniz = tk.Button(btn_islem, text="Tümünü Temizle", command=self.detay_onizleme_temizle, pady=5)
        btn_temizle_oniz.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.style_button(btn_temizle_oniz, "#475569", "#FFFFFF", "#334155", font_size=10)
        tree_frame = tk.Frame(onizleme_card, bg=bg_card)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))

        vsb_oniz = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb_oniz.pack(side=tk.RIGHT, fill='y')

        self.tree_onizleme = ttk.Treeview(tree_frame, columns=("Tarih", "Tür", "Gün"), show="headings", yscrollcommand=vsb_oniz.set)
        vsb_oniz.config(command=self.tree_onizleme.yview)

        self.tree_onizleme.heading("Tarih", text="Tarih", anchor=tk.W)
        self.tree_onizleme.heading("Tür", text="Tür", anchor=tk.W)
        self.tree_onizleme.heading("Gün", text="Süre", anchor=tk.W)
        self.tree_onizleme.column("Tarih", width=100, anchor=tk.W)
        self.tree_onizleme.column("Tür", width=60, anchor=tk.W)
        self.tree_onizleme.column("Gün", width=60, anchor=tk.W)
        self.tree_onizleme.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()

    def ay_degistir(self, artis):
        self.cal_month += artis
        if self.cal_month > 12: self.cal_month = 1; self.cal_year += 1
        elif self.cal_month < 1: self.cal_month = 12; self.cal_year -= 1
        self.takvimi_ciz()

    def takvimi_ciz(self):
        for widget in self.grid_frame.winfo_children(): widget.destroy()
        
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        gunler = ["Pzt", "Sal", "Çar", "Per", "Cum"] 
        self.lbl_ay_yil.config(text=f"{aylar[self.cal_month]} {self.cal_year}")

        bg_card = "#1E293B" if self.is_dark_mode else "#FFFFFF"
        fg_main = "#F8FAFC" if self.is_dark_mode else "#1E293B"
        cell_bg = "#334155" if self.is_dark_mode else "#F8FAFC"
        border_col = "#475569" if self.is_dark_mode else "#CBD5E1"

        for i in range(5):
            self.grid_frame.columnconfigure(i, weight=1)

        for c, gun in enumerate(gunler):
            tk.Label(self.grid_frame, text=gun, font=(UI_FONT, 11, "bold"), bg=bg_card, fg=fg_main).grid(row=0, column=c, pady=(0, 10), sticky="ew")

        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        aylik_dev = {}
        
        tum_devamsizliklar = getattr(self, 'secili_ogrenci_devamsizliklari', []) + self.gecici_devamsizliklar
        for dev in tum_devamsizliklar:
            if str(dev['no']).strip() == ogr_no_kati:
                if dev['tur'].upper() not in ["D", "ÖY", "SY"]: continue 
                
                try: gun_miktari = float(self.temiz_sure(dev['gun']))
                except: gun_miktari = 0.0
                tam_gun = int(gun_miktari) if gun_miktari >= 1 else 1
                    
                try:
                    d, m, y = map(int, self.tarih_formatla(dev['tarih']).split('/'))
                    baslangic_tarihi = datetime(y, m, d)
                    
                    # Devamsızlık kaç gün sürdüyse o kadar gün ileri giderek takvimi doldurur
                    for i in range(tam_gun):
                        g_tarih = baslangic_tarihi + timedelta(days=i)
                        
                        if g_tarih.month == self.cal_month and g_tarih.year == self.cal_year:
                            # Sadece Pzt-Cuma (0-4) arasını takvime ekler, hafta sonu boşluk bırakır
                            if g_tarih.weekday() < 5:
                                aylik_dev[g_tarih.day] = dev
                except: pass

        cal_data = calendar.monthcalendar(self.cal_year, self.cal_month)
        for r, week in enumerate(cal_data):
            self.grid_frame.rowconfigure(r+1, weight=1) 
            for c in range(5): 
                day = week[c]
                if day != 0:
                    frm = tk.Frame(self.grid_frame, bg=cell_bg, highlightbackground=border_col, highlightthickness=1)
                    frm.grid(row=r+1, column=c, padx=3, pady=3, sticky="nsew"); frm.pack_propagate(False)
                    
                    lbl_day = tk.Label(frm, text=str(day), font=(UI_FONT, 10, "bold"), bg=cell_bg, fg=fg_main)
                    lbl_day.pack(anchor=tk.NW, padx=6, pady=4)

                    if day in aylik_dev:
                        dev = aylik_dev[day]
                        tur = dev['tur'].upper()
                        is_ozursuz = tur in ["D", "ÖY", "SY"]
                        
                        box_bg = "#FEE2E2" if not self.is_dark_mode else "#7F1D1D"
                        box_fg = "#991B1B" if not self.is_dark_mode else "#FEF2F2"

                        if dev.get('secili'): frm.config(highlightbackground="#10B981", highlightthickness=3) 

                        frm.config(bg=box_bg); lbl_day.config(bg=box_bg, fg=box_fg)
                        gun_str = self.temiz_sure(dev['gun'])
                        lbl_info = tk.Label(frm, text=f"{gun_str} {tur}", font=(UI_FONT, 11, "bold"), bg=box_bg, fg=box_fg)
                        lbl_info.pack(expand=True)
                        
                        for w in [frm, lbl_day, lbl_info]:
                            if str(dev['id']).startswith('temp_'):
                                # Geçici kayıtsa sol tıkla tür döngüsü, sağ tıkla sil
                                w.bind("<Button-1>", lambda e, d=day: self.gecici_devamsizlik_dongu(d))
                                w.bind("<Button-3>", lambda e, d=day: self.gecici_devamsizlik_sil(d))
                            else:
                                # Veritabanından gelen kalıcı kayıtsa sadece seç/çıkar
                                w.bind("<Button-1>", lambda e, d=dev, f=frm: self.takvimden_onizlemeye_ekle(d, f))
                    else:
                        # Boş güne sol tıklayınca döngüyü başlat
                        lbl_day.bind("<Button-1>", lambda e, d=day: self.gecici_devamsizlik_dongu(d))
                        frm.bind("<Button-1>", lambda e, d=day: self.gecici_devamsizlik_dongu(d))

    def takvimden_onizlemeye_ekle(self, dev, frm):
        dev['secili'] = not dev.get('secili', False) 
        
        # Takvimi baştan çizmek yerine sadece kutunun çerçevesini yeşil yap
        # Bu sayede widget silinmez ve Çift Tıklama (<Double-1>) algılanabilir.
        if dev.get('secili'):
            frm.config(highlightbackground="#10B981", highlightthickness=3)
        else:
            border_col = "#475569" if self.is_dark_mode else "#CBD5E1"
            frm.config(highlightbackground=border_col, highlightthickness=1)
                 
        self.detay_onizlemeyi_guncelle()

    def toplu_secim_yap(self, mod):
        if not self.secili_ogrenci: return
        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        
        baslangic, bitis = None, None

        if mod == "bu_ay": 
            # Takvimde o an açık olan ayın 1'i ile son günü arasını tam kapsar
            son_gun = calendar.monthrange(self.cal_year, self.cal_month)[1]
            baslangic = datetime(self.cal_year, self.cal_month, 1)
            bitis = datetime(self.cal_year, self.cal_month, son_gun, 23, 59, 59)
            
        elif mod == "son_iki_ay": 
            # Takvimde açık olan ay ve bir önceki ayı kapsar
            son_gun = calendar.monthrange(self.cal_year, self.cal_month)[1]
            bitis = datetime(self.cal_year, self.cal_month, son_gun, 23, 59, 59)
            if self.cal_month == 1:
                baslangic = datetime(self.cal_year - 1, 12, 1)
            else:
                baslangic = datetime(self.cal_year, self.cal_month - 1, 1)
                
        elif mod == "aralik":
            if TKCALENDAR_VAR and hasattr(self, 'cal_bas'):
                try:
                    baslangic = datetime.combine(self.cal_bas.get_date(), datetime.min.time())
                    bitis = datetime.combine(self.cal_bit.get_date(), datetime.max.time())
                except Exception as e: 
                    self.bildirim_goster("Tarih seçimi hatalı!", "hata")
                    return
            else:
                try:
                    baslangic = datetime.strptime(self.cal_bas_ent.get().strip(), "%d/%m/%Y")
                    bitis = datetime.strptime(self.cal_bit_ent.get().strip(), "%d/%m/%Y")
                    bitis = bitis.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    self.bildirim_goster("Tarih formatı hatalı. (Örn: 01/05/2025)", "hata")
                    return

        for dev in getattr(self, 'secili_ogrenci_devamsizliklari', []) + self.gecici_devamsizliklar:
            dev['secili'] = False

        eklenen = 0
        for dev in getattr(self, 'secili_ogrenci_devamsizliklari', []):
            if str(dev['no']).strip() == ogr_no_kati:
                if dev['tur'].upper() not in ["D", "ÖY", "SY"]: 
                    continue 
                    
                if mod == "tumu":
                    dev['secili'] = True; eklenen += 1
                else:
                    d_tarih = self._parse_tarih(self.tarih_formatla(dev['tarih']))
                    if d_tarih and baslangic <= d_tarih <= bitis:
                        dev['secili'] = True; eklenen += 1
        
        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()
        
        if eklenen > 0: self.bildirim_goster(f"{eklenen} kayıt önizlemeye eklendi.", "bilgi")
        else: self.bildirim_goster("Seçilen aralıkta özürsüz devamsızlık bulunamadı.", "hata")

    def gecici_devamsizlik_dongu(self, day):
        tarih_str = f"{day:02d}/{self.cal_month:02d}/{self.cal_year}"
        ogr_no = str(self.secili_ogrenci['no']).strip()
        
        # Bu tarihte geçici bir kayıt var mı kontrol et
        mevcut_dev = None
        for dev in self.gecici_devamsizliklar:
            if dev['tarih'] == tarih_str and str(dev['no']).strip() == ogr_no:
                mevcut_dev = dev
                break
                
        if not mevcut_dev:
            # 1. TIKLAMA: Boş gün -> 1 Gün "D" yap
            yeni_dev = {'id': f"temp_{uuid.uuid4().hex}", 'no': ogr_no, 'tarih': tarih_str, 'tur': "D", 'gun': "1", 'secili': True}
            self.gecici_devamsizliklar.append(yeni_dev)
        else:
            # 2. TIKLAMA: D ise -> 0.5 Gün "SY" yap
            if mevcut_dev['tur'] == "D":
                mevcut_dev['tur'] = "SY"
                mevcut_dev['gun'] = "0.5"
            # 3. TIKLAMA: SY ise -> 0.5 Gün "ÖY" yap
            elif mevcut_dev['tur'] == "SY":
                mevcut_dev['tur'] = "ÖY"
                mevcut_dev['gun'] = "0.5"
            # 4. TIKLAMA: ÖY ise -> Sil ve Boş güne dön
            elif mevcut_dev['tur'] == "ÖY":
                self.gecici_devamsizliklar.remove(mevcut_dev)
                
        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()

    def gecici_devamsizlik_sil(self, day):
        # SAĞ TIKLAMA: Anında sil ve boş güne dön
        tarih_str = f"{day:02d}/{self.cal_month:02d}/{self.cal_year}"
        ogr_no = str(self.secili_ogrenci['no']).strip()
        
        self.gecici_devamsizliklar = [d for d in self.gecici_devamsizliklar if not (d['tarih'] == tarih_str and str(d['no']).strip() == ogr_no)]
        self.bildirim_goster("Geçici kayıt silindi.", "bilgi")
        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()

    def detay_onizlemeyi_guncelle(self):
        self.tree_onizleme.delete(*self.tree_onizleme.get_children())
        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        
        tum_kayitlar = getattr(self, 'secili_ogrenci_devamsizliklari', []) + self.gecici_devamsizliklar
        sirali_devamsizlik = sorted([d for d in tum_kayitlar if d.get('secili', False)], key=lambda x: self._parse_tarih(self.tarih_formatla(x['tarih'])) or datetime.min, reverse=True)
        
        toplam_gun = 0.0
        for dev in sirali_devamsizlik:
            gun_str = self.temiz_sure(dev['gun'])
            tarih_duzgun = self.tarih_formatla(dev['tarih'])
            self.tree_onizleme.insert("", tk.END, values=(tarih_duzgun, dev['tur'], gun_str), tags=(str(dev['id']),))
            try: toplam_gun += float(gun_str)
            except: pass
        
        toplam_str = int(toplam_gun) if toplam_gun.is_integer() else toplam_gun
        self.lbl_detay_ozet.config(text=f"Toplam: {toplam_str} Gün")
        self.btn_detay_pdf.config(state=tk.NORMAL if sirali_devamsizlik else tk.DISABLED)

    def detay_onizleme_cikar(self):
        secim = self.tree_onizleme.selection()
        if not secim: return
        ids_to_remove = [self.tree_onizleme.item(iid, "tags")[0] for iid in secim]
        
        for dev in self.devamsizlik_listesi + self.gecici_devamsizliklar:
            if str(dev['id']) in ids_to_remove: dev['secili'] = False
            
# Gecici olanları id'sinden tanı ve listeden at
        self.gecici_devamsizliklar = [d for d in self.gecici_devamsizliklar if d.get('secili', False)]
        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()

        # --- AYARLAR MENÜSÜ ---
     
    # --- AYARLAR MENÜSÜ VE YEDEKLEME SİSTEMİ ---
    

    # --- TAMAMLANMIŞ VE ÇALIŞAN YEDEK YÜKLE FONKSİYONU ---
    def yedek_yukle(self):
        # Ayarlardan seçilen klasörü al, yoksa varsayılanı kullan
        yedek_klasor = self.ayarlar.get("yedek_kayit_klasoru", "")
        if not yedek_klasor or not os.path.exists(yedek_klasor):
            yedek_klasor = os.path.join(GUVENLI_KLASOR, "Yedekler")
            
        if not os.path.exists(yedek_klasor):
            self.bildirim_goster("Belirtilen konumda yedek klasörü bulunmuyor.", "hata")
            return

        dosya_yolu = filedialog.askopenfilename(
            initialdir=yedek_klasor,
            title="Yedek Dosyası Seçin",
            filetypes=[("Veritabanı Yedekleri", "*.db"), ("Tüm Dosyalar", "*.*")]
        )

        if dosya_yolu:
            cevap = messagebox.askyesno("Yedek Yükle", "Mevcut veriler silinecek ve seçilen yedekteki veriler yüklenecek.\n\nBu işlemi onaylıyor musunuz?")
            if cevap:
                try:
                    self.db.kapat() 
                    shutil.copy(dosya_yolu, VERI_DOSYASI_DB) 
                    self.db.baglan_ve_hazirla()
                    self.verileri_yukle() 
                    
                    self.sube_listesini_guncelle()
                    self.ogrenci_tablosunu_doldur()
                    if self.secili_ogrenci: 
                        self.detay_paneli_ciz()
                        
                    self.bildirim_goster("Yedek başarıyla yüklendi.", "bilgi")
                    if hasattr(self, 'ayar_win') and self.ayar_win.winfo_exists(): 
                        self.ayar_win.destroy()
                        
                except Exception as e:
                    messagebox.showerror("Hata", f"Yedek yüklenirken hata oluştu:\n{e}")
                    self.db.baglan_ve_hazirla()
    def ayarlari_kaydet(self):
        SistemMotoru.ayarlari_kaydet(AYARLAR_DOSYASI, self.ayarlar)

    def ayarlari_yukle(self):
        self.ayarlar.update(SistemMotoru.ayarlari_yukle(AYARLAR_DOSYASI))
        self.logo_kontrol_et()

    def manuel_yedek_al(self, otomatik=False):
        if hasattr(self, 'db') and self.db.conn: self.db.conn.commit() 
        
        basarili, hata = SistemMotoru.yedek_al(VERI_DOSYASI_DB, self.ayarlar, YEDEK_KLASORU_VARSAYILAN)
        if basarili:
            self.ayarlar["son_yedekleme_gunu"] = datetime.now().strftime("%Y-%m-%d")
            self.ayarlari_kaydet()
            mesaj = "Zamanlanmış otomatik yedek alındı." if otomatik else "Veritabanı başarıyla yedeklendi!"
            self.bildirim_goster("Veritabanı yedeklendi.", "bilgi")
        else:
            if not otomatik: messagebox.showerror("Yedekleme Hatası", f"Hata:\n{hata}")

    def eski_yedekleri_temizle(self):
        # İşlem zaten yedek_al motorunun içinde yapılıyor, ama köprü bozulmasın diye buraya yönlendiriyoruz:
        SistemMotoru.eski_yedekleri_temizle(self.ayarlar, YEDEK_KLASORU_VARSAYILAN)
    
    def zamanlanmis_yedek_kontrolu(self):
        try:
            su_an = datetime.now()
            saat_str = su_an.strftime("%H:%M")
            bugun_str = su_an.strftime("%Y-%m-%d")
            
            ayar_saat = self.ayarlar.get("yedek_saati", "17:00")
            if len(ayar_saat) == 4 and ":" in ayar_saat: ayar_saat = "0" + ayar_saat # 9:00 ise 09:00 yapar
            
            # Ayarlanan saate geldiysek kontrol et
            if saat_str == ayar_saat:
                son_yedek = self.ayarlar.get("son_yedekleme_gunu", "")
                
                # Eğer bugün henüz yedek almadıysa
                if son_yedek != bugun_str: 
                    siklik = self.ayarlar.get("yedek_sikligi", "Her Gün")
                    yedekle = False
                    
                    if not son_yedek:
                        yedekle = True
                    else:
                        son_tarih = datetime.strptime(son_yedek, "%Y-%m-%d")
                        fark_gun = (su_an - son_tarih).days
                        
                        if siklik == "Her Gün" and fark_gun >= 1: yedekle = True
                        elif siklik == "Özel Gün" and fark_gun >= int(self.ayarlar.get("yedek_gun_sayisi", "3")): yedekle = True
                        elif siklik == "Haftada 1" and fark_gun >= 7: yedekle = True
                        elif siklik == "Ayda 1" and fark_gun >= 30: yedekle = True
                    
                    if yedekle:
                        self.manuel_yedek_al(otomatik=True)
        except: pass
        
        # Arka planda kendini her 60 saniyede bir çağırarak saati kontrol eder
        self.root.after(60000, self.zamanlanmis_yedek_kontrolu)
        # ... (fonksiyonun devamı) ...
    # Fonksiyon dışarı çıkarıldı ve hizalaması düzeltildi
    
    def detay_onizleme_temizle(self):
        if not self.secili_ogrenci: return
        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        
        # Sadece veritabanı kayıtlarını seçilmemiş yap (50 bin satır yerine 30 satır taranır)
        for dev in getattr(self, 'secili_ogrenci_devamsizliklari', []):
            dev['secili'] = False
                
        self.gecici_devamsizliklar = [d for d in self.gecici_devamsizliklar if str(d['no']).strip() != ogr_no_kati]
        self.takvimi_ciz()
        self.detay_onizlemeyi_guncelle()
        
# --- THREAD METOTLARI (Asenkron Excel Yükleme) ---
        # --- YARDIM VE KULLANIM KILAVUZU ---
    def goster_yukleme_penceresi(self, baslik):
        win = tk.Toplevel(self.root)
        win.title(baslik); win.geometry("350x120"); win.transient(self.root); win.grab_set(); win.resizable(False, False)
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175; y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
        win.geometry(f"+{x}+{y}")
        tk.Label(win, text="Lütfen bekleyin, veriler işleniyor...", font=(UI_FONT, 10, "bold"), fg="#1E293B").pack(pady=(20, 10))
        bar = ttk.Progressbar(win, mode='indeterminate'); bar.pack(fill=tk.X, padx=20); bar.start(15)
        return win

    def ogrenci_yukle_thread(self):
        dosya_yolu = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        if not dosya_yolu: return
        win = self.goster_yukleme_penceresi("Öğrenci Yükleniyor")
        
        def islem():
            # İşi yeni motorumuza devrediyoruz!
            yeni_liste, hata = ExcelMotoru.ogrenci_oku(dosya_yolu, self.ogrenci_listesi)
            if hata:
                self.root.after(0, lambda: self.hata_goster(win, hata))
            else:
                self.root.after(0, lambda: self.ogrenci_yukle_tamam(win, yeni_liste))
                
        threading.Thread(target=islem, daemon=True).start()
    def ogrenci_yukle_tamam(self, win, yeni):
        win.destroy()
        if yeni:
            self.ogrenci_listesi.extend(yeni); self.verileri_kaydet()
            self.sube_listesini_guncelle(); self.ogrenci_tablosunu_doldur()
            self.bildirim_goster(f"{len(yeni)} yeni öğrenci eklendi.", "bilgi")
        else: self.bildirim_goster("Geçerli yeni öğrenci bulunamadı.", "hata")

    def devamsizlik_yukle_thread(self):
        dosya_yolu = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        if not dosya_yolu: return
        win = self.goster_yukleme_penceresi("Devamsızlık Yükleniyor")
        
        def islem():
            # İşi yeni motorumuza devrediyoruz!
            yeni_liste, eklenen, hata = ExcelMotoru.devamsizlik_oku(dosya_yolu, self.devamsizlik_listesi)
            if hata:
                self.root.after(0, lambda: self.hata_goster(win, hata))
            else:
                self.root.after(0, lambda: self.devamsizlik_yukle_tamam(win, yeni_liste, eklenen))
                
        threading.Thread(target=islem, daemon=True).start()

    def devamsizlik_yukle_tamam(self, win, yeni, eklenen):
        win.destroy()
        if eklenen > 0:
            self.devamsizlik_listesi.extend(yeni); self.verileri_kaydet(); self.ogrenci_tablosunu_doldur()
            if self.secili_ogrenci: self.detay_paneli_ciz()
            
            # 1. Bildirim: Yükleme Başarılı (Yeşil)
            self.bildirim_goster(f"{eklenen} devamsızlık kaydedildi.", "bilgi")
            
            # --- 9 GÜNÜ AŞANLARI KONTROL SİSTEMİ ---
            siniri_asanlar = 0
            for ogr in self.ogrenci_listesi:
                ozsz, ozrl = self.hesapla_devamsizlik(ogr['no'])
                if ozsz > 9:  # Özürsüz devamsızlık 9 günü GEÇMİŞSE
                    siniri_asanlar += 1
                    
            if siniri_asanlar > 0:
                # 2. Bildirim: İlk yeşil bildirimin ekrandan gitmesi için 3 saniye (3000 ms) bekleyip kırmızı uyarıyı indiriyoruz.
                uyari_mesaji = f"DİKKAT: {siniri_asanlar} öğrencinin özürsüz devamsızlığı 9 günü geçmiştir!"
                self.root.after(3000, lambda: self.bildirim_goster(uyari_mesaji, "hata"))
                
        else: 
            self.bildirim_goster("Yeni devamsızlık bulunamadı!", "hata")

    def hata_goster(self, win, h): win.destroy(); messagebox.showerror("Hata", str(h))

    # --- PDF EXPORT SİSTEMİ (RESMİ A5 VELİ FORMU) ---
    def pdf_ciktisi_al(self):
        if not self.secili_ogrenci: return
        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        
        secili_idler = [self.tree_onizleme.item(iid, "tags")[0] for iid in self.tree_onizleme.get_children()]
        if not secili_idler:
            self.bildirim_goster("Önizleme listesi boş. Takvimden ekleyin.", "hata")
            return

        tum_kayitlar = self.devamsizlik_listesi + self.gecici_devamsizliklar
        secili_kayitlar = [d for d in tum_kayitlar if d['id'] in secili_idler]
        secili_kayitlar = sorted(secili_kayitlar, key=lambda x: self._parse_tarih(self.tarih_formatla(x['tarih'])) or datetime.min)

        ana_klasor = self.ayarlar.get("pdf_kayit_klasoru", "")
        if not ana_klasor or not os.path.exists(ana_klasor):
            self.bildirim_goster("Önce Ayarlar menüsünden PDF kayıt klasörünü seçin.", "hata")
            if hasattr(self, 'ayarlar_penceresi_ac'): self.ayarlar_penceresi_ac()
            return

        kisa_sube = self.kisa_sube_adi(self.secili_ogrenci['sube'])
        sube_temiz = kisa_sube.replace("/", "-").replace("\\", "-").replace(":", "").strip()
        sube_klasoru = os.path.join(ana_klasor, sube_temiz)
        if not os.path.exists(sube_klasoru): os.makedirs(sube_klasoru)
        
        base_isim = f"{ogr_no_kati}_{self.secili_ogrenci['ad_soyad'].replace(' ', '_')}"
        kayit_yeri = os.path.join(sube_klasoru, f"{base_isim}.pdf")
        
        sayac = 1
        while os.path.exists(kayit_yeri):
            kayit_yeri = os.path.join(sube_klasoru, f"{base_isim}_({sayac}).pdf")
            sayac += 1

        # Yeni matbaamız (PDF Motoru) için verileri hazırlıyoruz
        islenmis_kayitlar = []
        for kayit in secili_kayitlar:
            islenmis_kayitlar.append({
                'tarih_duzgun': self.tarih_formatla(kayit['tarih']),
                'tur': kayit['tur'],
                'gun_str': self.temiz_sure(kayit['gun'])
            })

        try:
            # BÜTÜN O KARMAŞIK ÇİZİM İŞLEMİ SADECE BU 2 SATIRA DÜŞTÜ!
            motor = PDFYoneticisi(self.ayarlar)
            motor.veli_formu_ciz(ogr_no_kati, self.secili_ogrenci['ad_soyad'], kisa_sube, islenmis_kayitlar, kayit_yeri)

            self.gecici_devamsizliklar = []
            self.takvimi_ciz()
            self.detay_onizlemeyi_guncelle()
            self.bildirim_goster("PDF başarıyla oluşturuldu.", "bilgi")
            
            if os.name == 'nt': os.startfile(kayit_yeri)
            
        except Exception as e: 
            self.bildirim_goster(f"PDF hatası: {e}", "hata")
            print(f"PDF Hatası: {e}")  
     # --- YAZI TEBLİĞİ PERSONEL YÜKLEME MOTORU ---
    # --- YAZI TEBLİĞİ PERSONEL YÜKLEME MOTORU (GÜNCELLENMİŞ) ---
    
   # --- YAZI TEBLİĞİ PERSONEL YÜKLEME & FİLTRE MOTORU ---
    # --- YAZI TEBLİĞİ PERSONEL YÜKLEME & FİLTRE MOTORU (DİNAMİK BAŞLIK RADARLI) ---
    # --- YAZI TEBLİĞİ: VERİTABANI BAĞLANTILI EXCEL YÜKLEME ---
    # --- YAZI TEBLİĞİ: VERİTABANI BAĞLANTILI EXCEL YÜKLEME ---
    def personel_yukle_motoru(self):
        dosya_yolu = filedialog.askopenfilename(title="Personel Excel Listesini Seçin", filetypes=[("Excel", "*.xlsx *.xls")])
        if not dosya_yolu: return
        self.ayarlar["son_personel_excel"] = dosya_yolu
        self.ayarlari_kaydet()
        # Göreve bakarak grubunu tahmin eden yapay zeka
        def grubu_tahmin_et(g):
            g_upper = str(g).upper()
            if "ÖĞRETMEN" in g_upper: return "Öğretmenler"
            if g_upper in ["OKUL MÜDÜRÜ", "MÜDÜR YARDIMCISI", "MÜDÜR BAŞYARDIMCISI", "VHKİ", "MEMUR"]: return "İdare"
            return "Diğer Personel"

        try:
            import pandas as pd
            df_temp = pd.read_excel(dosya_yolu, header=None)
            header_idx = 0
            for i, row in df_temp.iterrows():
                satir_metni = " ".join([str(x).upper() for x in row.values if pd.notna(x)])
                if "AD" in satir_metni and "SOYAD" in satir_metni:
                    header_idx = i; break
                    
            df = pd.read_excel(dosya_yolu, header=header_idx)
            df.columns = df.columns.str.strip().str.upper()
            
            ad_sutunu = 'AD SOYAD' if 'AD SOYAD' in df.columns else 'ADI SOYADI' if 'ADI SOYADI' in df.columns else None
            if not ad_sutunu:
                self.bildirim_goster("Excel'de 'Ad Soyad' başlığı bulunamadı!", "hata"); return
                
            yeni_personeller = []
            for index, row in df.iterrows():
                ad = str(row[ad_sutunu]).strip()
                gorev = "-"
                if 'GÖREVI' in df.columns: gorev = str(row['GÖREVI']).strip()
                elif 'GÖREVİ' in df.columns: gorev = str(row['GÖREVİ']).strip()
                
                brans = "-"
                if 'BRANŞI' in df.columns: brans = str(row['BRANŞI']).strip()
                elif 'BRANSI' in df.columns: brans = str(row['BRANSI']).strip()
                
                if not brans or brans.lower() == 'nan': brans = "-"
                if not gorev or gorev.lower() == 'nan': gorev = "-"
                
                if ad and ad.lower() != 'nan' and ad != 'NAN':
                    grup = grubu_tahmin_et(gorev)
                    yeni_personeller.append((ad, brans, gorev, grup))
            
            self.db.cursor.execute("DELETE FROM personel")
            self.db.cursor.executemany("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", yeni_personeller)
            self.db.conn.commit()
            
            self.personel_listesi = [{'ad': p[0], 'brans': p[1], 'gorev': p[2], 'grup': p[3], 'haric': False} for p in yeni_personeller]
            self.filtreleri_guncelle()
            self.teblig_onizleme_guncelle()
            self.gruplari_guncelle()
            self.bildirim_goster(f"{len(self.personel_listesi)} personel yüklendi ve gruplandırıldı.", "bilgi")
        except Exception as e:
            self.bildirim_goster(f"Kayıt Hatası:\n{e}", "hata")

        self.bireysel_teblig_isimleri_guncelle()
        self.dinamik_filtreleri_guncelle()

    def teblig_onizleme_guncelle(self):
        if not hasattr(self, 'tree_teblig_onizleme'): return
        self.tree_teblig_onizleme.delete(*self.tree_teblig_onizleme.get_children())
        
        grup = self.combo_teblig_grup.get() if hasattr(self, 'combo_teblig_grup') else "Tümü"
        
        # Boş satır istenmişse ekrana sadece boşluklar basıp PDF'i buna hazırlarız
        if grup == "Boş Satır":
            for _ in range(15): # 15 Adet Boş Satır
                self.tree_teblig_onizleme.insert("", tk.END, values=("", "", ""))
            if hasattr(self, 'lbl_teblig_sayi'): self.lbl_teblig_sayi.config(text="15 Boş Satır")
            return
            
        brans = self.combo_teblig_brans.get() if hasattr(self, 'combo_teblig_brans') else "Tümü"
        
        gosterilecekler = []
        for p in getattr(self, 'personel_listesi', []):
            if p.get('haric', False): continue
            
            # Filtreleme Mantığı
            if grup != "Tümü" and p.get('grup') != grup: continue
            if grup == "Öğretmenler" and brans != "Tümü" and p.get('brans', '-') != brans: continue
                
            gosterilecekler.append(p)
            
        def grup_sirasi(g):
            if g == "İdare": return 1
            elif g == "Öğretmenler": return 2
            else: return 3
            
        gosterilecekler.sort(key=lambda x: (grup_sirasi(x.get('grup', 'Diğer Personel')), x.get('ad', '')))
        
        for p in gosterilecekler:
            # İŞTE KİLİT NOKTA BURASI: 3 Ayrı Sütun (Görev, Branş, Ad Soyad) tam yerine oturuyor!
            self.tree_teblig_onizleme.insert("", tk.END, values=(p.get('gorev', '-'), p.get('brans', '-'), p.get('ad', '')))
            
        if hasattr(self, 'lbl_teblig_sayi'):
            self.lbl_teblig_sayi.config(text=f"{len(gosterilecekler)} Kişi")

    # --- DİNAMİK FİLTRE VE ÖNİZLEME BUTON MOTORLARI ---
    def filtreleri_guncelle(self):
        branslar = set([p.get('brans', '-') for p in getattr(self, 'personel_listesi', []) if p.get('brans', '-') != '-'])
        gorevler = set([p.get('gorev', '-') for p in getattr(self, 'personel_listesi', []) if p.get('gorev', '-') != '-'])
        
        if hasattr(self, 'combo_teblig_brans'):
            self.combo_teblig_brans['values'] = ["Tüm Branşlar"] + sorted(list(branslar))
            try: self.combo_teblig_brans.current(0)
            except: pass
            
        if hasattr(self, 'combo_teblig_gorev'):
            self.combo_teblig_gorev['values'] = ["Tüm Görevler"] + sorted(list(gorevler))
            try: self.combo_teblig_gorev.current(0)
            except: pass

    def detay_onizleme_cikar(self):
        secim = self.tree_teblig_onizleme.selection()
        if not secim: return
        
        # Yeni sistemde Ad Soyad 3. sütunda (Yani index 2'de) yer alıyor
        cikarilacak_isimler = [self.tree_teblig_onizleme.item(iid, 'values')[2] for iid in secim]
        for p in getattr(self, 'personel_listesi', []):
            if p.get('ad') in cikarilacak_isimler:
                p['haric'] = True # Önizlemeden geçici olarak gizle
                
        self.teblig_onizleme_guncelle()

    def detay_onizleme_temizle(self):
        # Sağdaki listeden çıkarılan (İzinli/Raporlu) herkesi geri getirir
        for p in getattr(self, 'personel_listesi', []):
            p['haric'] = False
        self.teblig_onizleme_guncelle()
    
    # --- PERSONEL YÖNETİM PENCERESİ (EKSİKSİZ) ---
    def personel_yonetim_penceresi_ac(self):
        win = tk.Toplevel(self.root)
        win.title("Personel Yönetimi")
        win.geometry("450x550")
        win.configure(bg="#0F172A" if self.is_dark_mode else "#F1F5F9")
        win.grab_set()
        
        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ================= EKLE SEKMESİ =================
        sekme_ekle = tk.Frame(nb, padx=20, pady=20)
        nb.add(sekme_ekle, text="➕ Personel Ekle")
        
        # Dinamik Listeler (Sistem veritabanındaki her benzersiz kaydı bulur)
        m_gorevler = sorted(list(set([p.get('gorev', '-') for p in self.personel_listesi if p.get('gorev', '-') != '-'])))
        m_branslar = sorted(list(set([p.get('brans', '-') for p in self.personel_listesi if p.get('brans', '-') != '-'])))
        m_gruplar = sorted(list(set([p.get('grup', 'Diğer Personel') for p in self.personel_listesi])))
        if "Öğretmenler" in m_gruplar: m_gruplar.remove("Öğretmenler")
        if "İdare" in m_gruplar: m_gruplar.remove("İdare")
        m_gruplar = ["İdare", "Öğretmenler"] + m_gruplar # Resmi hiyerarşiyi koru
        
        tk.Label(sekme_ekle, text="Ad Soyad:", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        ent_ad = tk.Entry(sekme_ekle, font=(UI_FONT, 11), relief="solid", bd=1); ent_ad.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        # DİKKAT: State ayarları "normal". Listeden seçebilir VEYA yeni bir şey yazabilirsin!
        tk.Label(sekme_ekle, text="Görevi (Seç VEYA Yeni Yaz):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        combo_gorev = ttk.Combobox(sekme_ekle, values=m_gorevler, font=(UI_FONT, 11)); combo_gorev.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(sekme_ekle, text="Branşı (Seç VEYA Yeni Yaz):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        combo_brans = ttk.Combobox(sekme_ekle, values=m_branslar, font=(UI_FONT, 11)); combo_brans.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(sekme_ekle, text="Grubu (Seç VEYA Yeni Yaz):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        combo_grup = ttk.Combobox(sekme_ekle, values=m_gruplar, font=(UI_FONT, 11)); combo_grup.pack(fill=tk.X, ipady=4, pady=(0, 10))
        combo_grup.current(1)
        
        def kaydet():
            ad = ent_ad.get().strip().upper()
            gorev = combo_gorev.get().strip().upper() or "-"
            brans = combo_brans.get().strip().upper() or "-"
            # Yeni bir grup yazılırsa ilk harflerini büyüterek şık bir şekilde (Title Case) kaydet
            grup_raw = combo_grup.get().strip()
            grup = grup_raw.title() if grup_raw else "Diğer Personel"
            
            if not ad:
                self.bildirim_goster("Ad Soyad boş bırakılamaz!", "hata"); return
                
            self.db.cursor.execute("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", (ad, brans, gorev, grup))
            self.db.conn.commit()
            
            self.personel_listesi.append({'ad': ad, 'brans': brans, 'gorev': gorev, 'grup': grup, 'haric': False})
            self.gruplari_guncelle()
            self.grup_degisti_motoru()
            self.bildirim_goster(f"{ad} eklendi.", "bilgi")
            
            # EXCEL SENKRONİZASYON SORUSU
            if messagebox.askyesno("Excel'e İşlensin Mi?", f"{ad} sisteme eklendi.\nBu kayıt orijinal Excel dosyasına da yazılsın mı?", parent=win):
                self.excel_personel_guncelle("ekle", ad, brans, gorev)
                
            ent_ad.delete(0, tk.END); combo_gorev.set(""); combo_brans.set(""); combo_grup.current(1)
            liste_guncelle()
            self.dinamik_filtreleri_guncelle()

        btn_kaydet = tk.Button(sekme_ekle, text="💾 Kaydet ve Öğren", command=kaydet, pady=8)
        btn_kaydet.pack(fill=tk.X, pady=15)
        self.style_button(btn_kaydet, "#10B981", "#FFFFFF", "#059669")

        # ================= ÇIKAR SEKMESİ =================
        sekme_cikar = tk.Frame(nb, padx=15, pady=15)
        nb.add(sekme_cikar, text="➖ Personel Çıkar")
        
        arama_frame = tk.Frame(sekme_cikar)
        arama_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(arama_frame, text="İsim Ara:", font=(UI_FONT, 10, "bold")).pack(side=tk.LEFT)
        ent_ara = tk.Entry(arama_frame, font=(UI_FONT, 10), relief="solid", bd=1)
        ent_ara.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0), ipady=3)
        
        list_frame = tk.Frame(sekme_cikar)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        liste_kutu = tk.Listbox(list_frame, font=(UI_FONT, 11), yscrollcommand=scrollbar.set, selectbackground="#EF4444")
        liste_kutu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=liste_kutu.yview)
        
        def liste_guncelle(filtre_metni=""):
            liste_kutu.delete(0, tk.END)
            for p in sorted(self.personel_listesi, key=lambda x: x['ad']):
                if filtre_metni.upper() in p['ad'].upper(): liste_kutu.insert(tk.END, p['ad'])
                    
        ent_ara.bind("<KeyRelease>", lambda e: liste_guncelle(ent_ara.get()))
        
        def sil():
            secim = liste_kutu.curselection()
            if not secim: return
            secili_ad = liste_kutu.get(secim[0])
            
            if messagebox.askyesno("Kalıcı Silme", f"{secili_ad} veritabanından kalıcı silinecek. Onaylıyor musunuz?", parent=win):
                self.db.cursor.execute("DELETE FROM personel WHERE ad_soyad = ?", (secili_ad,))
                self.db.conn.commit()
                self.personel_listesi = [p for p in self.personel_listesi if p['ad'] != secili_ad]
                self.gruplari_guncelle()
                self.grup_degisti_motoru()
                liste_guncelle(ent_ara.get())
                self.bildirim_goster(f"{secili_ad} silindi.", "bilgi")
                
                # EXCEL SENKRONİZASYON SORUSU
                if messagebox.askyesno("Excel'den Silinsin Mi?", f"{secili_ad} programdan silindi.\nBu kayıt orijinal Excel dosyasından da kaldırılsın mı?", parent=win):
                    self.excel_personel_guncelle("sil", secili_ad)
                
        btn_sil = tk.Button(sekme_cikar, text="🗑️ Seçili Personeli Tamamen Sil", command=sil, pady=8)
        btn_sil.pack(fill=tk.X, pady=15)
        self.style_button(btn_sil, "#EF4444", "#FFFFFF", "#DC2626")
        
        liste_guncelle()
        self.dinamik_filtreleri_guncelle()

    # --- TEBLİĞ ÇIKTISI OLUŞTURMA MOTORU (GÖREV VE BRANŞ AYRILDI) ---
    def teblig_ciktisi_al(self):
        sayi = self.ent_teblig_sayi.get().strip()
        konu = self.ent_teblig_konu.get().strip()
        tarih = self.ent_teblig_tarih.get().strip()

        secili_personeller = []
        for item in self.tree_teblig_onizleme.get_children():
            degerler = self.tree_teblig_onizleme.item(item, 'values')
            secili_personeller.append({'gorev': degerler[0], 'brans': degerler[1], 'ad': degerler[2]})

        if not secili_personeller: return

        yol = filedialog.asksaveasfilename(initialfile=f"Teblig_Listesi_{datetime.now().strftime('%d_%m_%Y')}.pdf", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not yol: return
        win = self.goster_yukleme_penceresi("PDF Hazırlanıyor...")
        
        win = self.goster_yukleme_penceresi("Toplu İmza Listesi Hazırlanıyor...")
        
        def islem():
            try:
                motor = PDFYoneticisi(self.ayarlar)
                motor.teblig_tebellug_ciz(sayi, konu, tarih, secili_personeller, yol)
                
                self.root.after(0, lambda: self.rapor_tamam(win, yol, None, "Toplu imza listesi başarıyla oluşturuldu."))
            except Exception as e:
                # ZIRH: e değişkeni silinmeden önce string'e çevrilip lambda içine hapsoluyor
                err = str(e)
                self.root.after(0, lambda mesaj=err: self.hata_goster(win, f"PDF Hatası:\n{mesaj}"))
                
        import threading
        threading.Thread(target=islem, daemon=True).start()

    # --- YENİ NESİL EXCEL TARZI FİLTRE MOTORLARI ---
    def dinamik_filtreleri_guncelle(self):
        """Veritabanına yeni bir görev veya branş eklendiğinde filtreleri anında öğrenir ve günceller."""
        if not hasattr(self, 'personel_listesi'): return
        
        # Benzersiz görev ve branşları listele
        gorevler = sorted(list(set([p.get('gorev', '-') for p in self.personel_listesi if p.get('gorev', '-') != '-'])))
        branslar = sorted(list(set([p.get('brans', '-') for p in self.personel_listesi if p.get('brans', '-') != '-'])))
        
        # Mevcut tikleri hafızada tut, yeni gelenleri varsayılan olarak "Tikli" (True) yap
        if not hasattr(self, 'filtre_gorev_var'): self.filtre_gorev_var = {}
        if not hasattr(self, 'filtre_brans_var'): self.filtre_brans_var = {}
        
        self.filtre_gorev_var = {g: self.filtre_gorev_var.get(g, tk.BooleanVar(value=True)) for g in gorevler}
        self.filtre_brans_var = {b: self.filtre_brans_var.get(b, tk.BooleanVar(value=True)) for b in branslar}
        
        # Görev Menüsünü İnşa Et
        self.menu_gorev.delete(0, tk.END)
        self.menu_gorev.add_command(label="🔄 Tümünü Seç / Temizle", command=lambda: self.toplu_secim_yap(self.filtre_gorev_var))
        self.menu_gorev.add_separator()
        for g in gorevler:
            self.menu_gorev.add_checkbutton(label=g, variable=self.filtre_gorev_var[g], command=self.personel_tablosunu_doldur)
            
        # Branş Menüsünü İnşa Et
        self.menu_brans.delete(0, tk.END)
        self.menu_brans.add_command(label="🔄 Tümünü Seç / Temizle", command=lambda: self.toplu_secim_yap(self.filtre_brans_var))
        self.menu_brans.add_separator()
        for b in branslar:
            self.menu_brans.add_checkbutton(label=b, variable=self.filtre_brans_var[b], command=self.personel_tablosunu_doldur)
            
        self.personel_tablosunu_doldur()

    def toplu_secim_yap(self, filtre_sozlugu):
        """Excel'deki 'Tümünü Seç' kutusu gibi çalışır."""
        durumlar = [var.get() for var in filtre_sozlugu.values()]
        yeni_durum = not all(durumlar) # Hepsi tikliyse temizle, değilse hepsini tikle
        for var in filtre_sozlugu.values():
            var.set(yeni_durum)
        self.personel_tablosunu_doldur()

    def personel_tablosunu_doldur(self):
        """Arama çubuğu ve Checkbox filtrelerini çaprazlayarak tabloyu doldurur."""
        if not hasattr(self, 'tree_personel') or not hasattr(self, 'personel_listesi'): return
        self.tree_personel.delete(*self.tree_personel.get_children())
        
        arama_metni = self.ent_arama.get().strip().upper() if hasattr(self, 'ent_arama') else ""
        
        for p in self.personel_listesi:
            gorev = p.get('gorev', '-')
            brans = p.get('brans', '-')
            ad = p.get('ad', '')
            
            # 1. ZIRH: Arama Çubuğu (İsim, Görev veya Branşta harf bile geçse bulur)
            if arama_metni and (arama_metni not in ad.upper() and arama_metni not in gorev.upper() and arama_metni not in brans.upper()):
                continue
                
            # 2. ZIRH: Excel Tarzı Çoklu Filtreler (Tiki kaldırılmışları atlar)
            if hasattr(self, 'filtre_gorev_var') and gorev in self.filtre_gorev_var:
                if not self.filtre_gorev_var[gorev].get(): continue
            if hasattr(self, 'filtre_brans_var') and brans in self.filtre_brans_var:
                if not self.filtre_brans_var[brans].get(): continue
                
            tag = "secili" if p.get('durum', '[X]') == "[X]" else "haric"
            
            # Yeni ve Nizami 4 Sütun (Durum, Görev, Branş, Ad)
            self.tree_personel.insert("", tk.END, values=(p.get('durum', '[X]'), gorev, brans, ad), tags=(tag,))
            
        self.tree_personel.tag_configure('secili', background='#F0FDF4' if not self.is_dark_mode else '#064E3B', foreground='#166534' if not self.is_dark_mode else '#A7F3D0')
        self.tree_personel.tag_configure('haric', background='#FEF2F2' if not self.is_dark_mode else '#7F1D1D', foreground='#991B1B' if not self.is_dark_mode else '#FECACA')

    def personel_secim_toggle(self, event):
        item_id = self.tree_personel.identify_row(event.y)
        col_id = self.tree_personel.identify_column(event.x)
        
        if item_id and col_id == '#1': # Sadece Seçim (Durum) sütununa tıklanırsa çalış
            item = self.tree_personel.item(item_id)
            vals = list(item['values'])
            personel_adi = vals[3] # Ad artık 4. sütunda (İndeksi 3)
            
            yeni_durum = "[ ]" if vals[0] == "[X]" else "[X]"
            
            for p in self.personel_listesi:
                if p.get('ad') == personel_adi:
                    p['durum'] = yeni_durum
                    break
            self.personel_tablosunu_doldur()

    # --- YAZI TEBLİĞİ PDF OKUMA MOTORU ---
    def pdf_yukle_motoru(self):
        dosya_yolu = filedialog.askopenfilename(title="MEB Resmi Yazısını (PDF) Seçin", filetypes=[("PDF Dosyaları", "*.pdf")])
        if not dosya_yolu: return

        try:
            import PyPDF2
            import re

            with open(dosya_yolu, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                # DYS yazılarında ana bilgiler her zaman ilk sayfadadır
                ilk_sayfa = reader.pages[0].extract_text()

            # 1. TARİH DEDEKTİFİ (Örn: 29.06.2026 formatını arar)
            tarih_match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', ilk_sayfa)
            tarih = tarih_match.group(0) if tarih_match else ""

            # 2. SAYI DEDEKTİFİ (Örn: E-84692172-918.99-163211388 formatını arar)
            sayi_match = re.search(r'(E-\d+-\d+\.\d+-\d+)', ilk_sayfa)
            if not sayi_match:
                # DYS dışı eski formatlar için alternatif arama
                sayi_match = re.search(r'Sayı\s*[:\n]\s*([A-Za-z0-9\-.]+)', ilk_sayfa)
            sayi = sayi_match.group(1) if sayi_match else ""

            # 3. KONU DEDEKTİFİ (DYS'nin karmaşık yapısına uygun)
            konu = ""
            # "Konu :" veya alt satırına geçmiş metinleri "İlgi", "T.C." veya "DAĞITIM" kelimelerine kadar tarar
            konu_match = re.search(r'Konu\s*(?::|\n)(.*?)(?=\nİlgi|\nT\.C\.|\nDAĞITIM|\nOkul ve kurumlarda)', ilk_sayfa, re.DOTALL | re.IGNORECASE)
            
            if konu_match:
                # Bulunan metindeki yeni satırları ve gereksiz boşlukları temizle
                konu_ham = konu_match.group(1).strip()
                konu = " ".join(konu_ham.split())
                # Eğer "Sayı" ile ilgili bir veri karışmışsa (Örn: ": E-123... Çalışanların...") onu filtrele
                if sayi and sayi in konu:
                    konu = konu.replace(sayi, "").replace(":", "").strip()

            # 4. BİLGİLERİ KUTULARA YERLEŞTİRME
            self.ent_teblig_sayi.delete(0, tk.END)
            self.ent_teblig_sayi.insert(0, sayi)
            
            self.ent_teblig_konu.delete(0, tk.END)
            # Konu çok uzunsa ilk kısmını alıp gerisini düzeltmesi için öğretmene bırakırız
            self.ent_teblig_konu.insert(0, konu if len(konu) < 80 else konu[:80] + "...") 
            
            self.ent_teblig_tarih.delete(0, tk.END)
            self.ent_teblig_tarih.insert(0, tarih)
            
            self.bildirim_goster("PDF başarıyla analiz edildi.", "bilgi")

        except ImportError:
            self.bildirim_goster("PyPDF2 kütüphanesi eksik! Terminale 'pip install PyPDF2' yazıp Enter'a basın.", "hata")
        except Exception as e:
            self.bildirim_goster(f"PDF analiz edilirken hata oluştu:\n{e}", "hata")

    # --- YAZI TEBLİĞİ ÇIKTI ALMA MOTORU ---
    # --- TOPLU İMZA SİRKÜSÜ ÇIKTI MOTORU (GÜVENLİ) ---
    def teblig_ciktisi_al(self):
        sayi = self.ent_teblig_sayi.get().strip()
        konu = self.ent_teblig_konu.get().strip()
        tarih = self.ent_teblig_tarih.get().strip()

        # ZIRH EKLENDİ: p['durum'] yerine p.get('durum', '[X]') kullanılarak çökme önlendi
        secili_personeller = [p for p in getattr(self, 'personel_listesi', []) if p.get('durum', '[X]') == '[X]']

        if not secili_personeller:
            self.bildirim_goster("Lütfen listeden tebliğ edilecek en az bir personel seçin!", "hata")
            return

        otomatik_isim = f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y')}.pdf"
        yol = filedialog.asksaveasfilename(initialfile=otomatik_isim, defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Toplu İmza Sirküsünü Kaydet")
        
        if not yol: return

        win = self.goster_yukleme_penceresi("Toplu İmza Listesi Hazırlanıyor...")
        
        def islem():
            try:
                motor = PDFYoneticisi(self.ayarlar)
                motor.teblig_tebellug_ciz(sayi, konu, tarih, secili_personeller, yol)
                
                self.root.after(0, lambda: self.rapor_tamam(win, yol, None, "Toplu imza listesi başarıyla oluşturuldu."))
            except Exception as e:
                self.root.after(0, lambda: self.hata_goster(win, f"PDF Hatası:\n{e}"))
                
        import threading
        threading.Thread(target=islem, daemon=True).start()

    # --- İDARECİLERİ SÜZEN LİSTE MOTORU ---
    def bireysel_teblig_isimleri_guncelle(self):
        if not hasattr(self, 'combo_teblig_eden'): return
        
        tum_isimler = ["Seçiniz"] + sorted([p.get('ad', '') for p in getattr(self, 'personel_listesi', []) if p.get('ad')])
        
        idare_isimleri = ["Seçiniz"]
        for p in getattr(self, 'personel_listesi', []):
            gorev = str(p.get('gorev', '')).upper()
            grup = str(p.get('grup', '')).upper()
            
            # KİŞİ İDARE Mİ? (Grubu idare olanlar VEYA görevinde idari kelimeler geçenler)
            idari_kelimeler = ['MÜDÜR', 'YARDIMCI', 'İDARE', 'VHKİ', 'MEMUR', 'ŞEF', 'MEMURE']
            is_idare = (grup == 'İDARE') or any(k in gorev for k in idari_kelimeler)
            
            if is_idare:
                idare_isimleri.append(p.get('ad', ''))
                
        idare_isimleri = ["Seçiniz"] + sorted(list(set(idare_isimleri[1:])))
        if len(idare_isimleri) == 1: idare_isimleri = tum_isimler # Güvenlik: İdare hiç yoksa listeyi boş bırakma
        
        mevcut_eden = self.combo_teblig_eden.get()
        mevcut_edilen = self.combo_tebellug_eden.get()
        
        self.combo_teblig_eden['values'] = idare_isimleri # Tebliğ eden SADECE idare grubu
        self.combo_tebellug_eden['values'] = tum_isimler  # Tebellüğ eden herkes
        
        if mevcut_eden in idare_isimleri: self.combo_teblig_eden.set(mevcut_eden)
        else: self.combo_teblig_eden.current(0)
        
        if mevcut_edilen in tum_isimler: self.combo_tebellug_eden.set(mevcut_edilen)
        else: self.combo_tebellug_eden.current(0)

    # --- PERSONEL YÖNETİM PENCERESİ ---
    def personel_yonetim_penceresi_ac(self):
        win = tk.Toplevel(self.root)
        win.title("Personel Yönetimi")
        win.geometry("450x550")
        win.configure(bg="#0F172A" if self.is_dark_mode else "#F1F5F9")
        win.grab_set()
        
        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ====== EKLE SEKMESİ ======
        sekme_ekle = tk.Frame(nb, padx=20, pady=20)
        nb.add(sekme_ekle, text="➕ Ekle")
        
        tk.Label(sekme_ekle, text="Ad Soyad:", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        ent_ad = tk.Entry(sekme_ekle, font=(UI_FONT, 11), relief="solid", bd=1); ent_ad.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(sekme_ekle, text="Görevi (Müdür, VHKİ, Memur, Öğretmen vb.):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        ent_gorev = tk.Entry(sekme_ekle, font=(UI_FONT, 11), relief="solid", bd=1); ent_gorev.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(sekme_ekle, text="Branşı (Tarih, Matematik vb.):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        ent_brans = tk.Entry(sekme_ekle, font=(UI_FONT, 11), relief="solid", bd=1); ent_brans.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(sekme_ekle, text="Grubu (İdari Yetki İçin 'İdare' Seçin):", font=(UI_FONT, 10, "bold")).pack(anchor=tk.W)
        combo_grup = ttk.Combobox(sekme_ekle, values=["İdare", "Öğretmenler", "Diğer Personel"], state="readonly", font=(UI_FONT, 11))
        combo_grup.pack(fill=tk.X, ipady=4, pady=(0, 10))
        combo_grup.current(1)
        
        def kaydet():
            ad = ent_ad.get().strip().upper()
            gorev = ent_gorev.get().strip().upper() or "-"
            brans = ent_brans.get().strip().upper() or "-"
            grup = combo_grup.get()
            
            if not ad:
                self.bildirim_goster("Ad Soyad boş bırakılamaz!", "hata"); return
                
            try:
                # Veritabanına grup sütununu garantiye alarak ekle
                self.db.cursor.execute("PRAGMA table_info(personel)")
                if 'grup' not in [col[1] for col in self.db.cursor.fetchall()]:
                    self.db.cursor.execute("ALTER TABLE personel ADD COLUMN grup TEXT DEFAULT 'Diğer Personel'")
                
                self.db.cursor.execute("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", (ad, brans, gorev, grup))
                self.db.conn.commit()
            except: pass 
                
            self.personel_listesi.append({'ad': ad, 'brans': brans, 'gorev': gorev, 'grup': grup, 'durum': '[X]'})
            self.personel_tablosunu_doldur()
            self.bireysel_teblig_isimleri_guncelle() # İdareye eklendiyse anında kutuda belirir
            self.bildirim_goster(f"{ad} eklendi.", "bilgi")
            ent_ad.delete(0, tk.END); ent_gorev.delete(0, tk.END); ent_brans.delete(0, tk.END)
            liste_guncelle()

        btn_kaydet = tk.Button(sekme_ekle, text="💾 Kaydet", command=kaydet, pady=8)
        btn_kaydet.pack(fill=tk.X, pady=15)
        self.style_button(btn_kaydet, "#10B981", "#FFFFFF", "#059669")

        # ====== ÇIKAR SEKMESİ ======
        sekme_cikar = tk.Frame(nb, padx=15, pady=15)
        nb.add(sekme_cikar, text="➖ Çıkar")
        
        arama_frame = tk.Frame(sekme_cikar); arama_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(arama_frame, text="İsim Ara:", font=(UI_FONT, 10, "bold")).pack(side=tk.LEFT)
        ent_ara = tk.Entry(arama_frame, font=(UI_FONT, 10), relief="solid", bd=1); ent_ara.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0), ipady=3)
        
        list_frame = tk.Frame(sekme_cikar); list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        liste_kutu = tk.Listbox(list_frame, font=(UI_FONT, 11), yscrollcommand=scrollbar.set, selectbackground="#EF4444")
        liste_kutu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.config(command=liste_kutu.yview)
        
        def liste_guncelle(filtre_metni=""):
            liste_kutu.delete(0, tk.END)
            for p in sorted(self.personel_listesi, key=lambda x: x.get('ad', '')):
                if filtre_metni.upper() in p.get('ad', '').upper(): liste_kutu.insert(tk.END, p.get('ad', ''))
                    
        ent_ara.bind("<KeyRelease>", lambda e: liste_guncelle(ent_ara.get()))
        
        def sil():
            secim = liste_kutu.curselection()
            if not secim: return
            secili_ad = liste_kutu.get(secim[0])
            
            if messagebox.askyesno("Silme Onayı", f"{secili_ad} silinecek. Onaylıyor musunuz?", parent=win):
                self.db.cursor.execute("DELETE FROM personel WHERE ad_soyad = ?", (secili_ad,))
                self.db.conn.commit()
                self.personel_listesi = [p for p in getattr(self, 'personel_listesi', []) if p.get('ad') != secili_ad]
                self.personel_tablosunu_doldur()
                self.bireysel_teblig_isimleri_guncelle()
                liste_guncelle(ent_ara.get())
                self.bildirim_goster(f"{secili_ad} silindi.", "bilgi")
                
        btn_sil = tk.Button(sekme_cikar, text="🗑️ Seçili Personeli Sil", command=sil, pady=8)
        btn_sil.pack(fill=tk.X, pady=15)
        self.style_button(btn_sil, "#EF4444", "#FFFFFF", "#DC2626")
        
        liste_guncelle()

    def bireysel_teblig_ciktisi_al(self):
        sayi = self.ent_teblig_sayi.get().strip()
        konu = self.ent_teblig_konu.get().strip()
        tarih = self.ent_teblig_tarih.get().strip()
        
        eden_ad = self.combo_teblig_eden.get()
        edilen_ad = self.combo_tebellug_eden.get()
        t_yeri = self.ent_teblig_yeri.get().strip()
        
        if eden_ad == "Seçiniz" or edilen_ad == "Seçiniz":
            self.bildirim_goster("Lütfen tebliğ eden ve edilen kişileri seçin!", "hata")
            return
            
        t_eden = {'ad': eden_ad, 'gorev': ''}
        t_edilen = {'ad': edilen_ad, 'gorev': ''}
        
        # Seçilenlerin unvanlarını/görevlerini listeden otomatik çeker
        for p in getattr(self, 'personel_listesi', []):
            unvan = p.get('gorev', '-') if p.get('gorev', '-') != '-' else p.get('brans', 'Personel')
            if p['ad'] == eden_ad: t_eden['gorev'] = unvan
            if p['ad'] == edilen_ad: t_edilen['gorev'] = unvan
                
        otomatik_isim = f"Bireysel_Teblig_{edilen_ad.replace(' ', '_')}.pdf"
        yol = filedialog.asksaveasfilename(initialfile=otomatik_isim, defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Tebliğ Belgesini Kaydet")
        if not yol: return
        
        win = self.goster_yukleme_penceresi("Bireysel Tebliğ Hazırlanıyor...")
        
        def islem():
            try:
                motor = PDFYoneticisi(self.ayarlar)
                motor.bireysel_teblig_ciz(sayi, konu, tarih, t_eden, t_edilen, t_yeri, yol)
                self.root.after(0, lambda: self.rapor_tamam(win, yol, None, "Tebliğ belgesi başarıyla oluşturuldu."))
            except Exception as e:
                hata_mesaji = str(e) # KİLİT NOKTA: Hata silinmeden önce metne çeviriyoruz!
                self.root.after(0, lambda err=hata_mesaji: self.hata_goster(win, f"PDF Hatası:\n{err}"))
                
        import threading
        threading.Thread(target=islem, daemon=True).start()

# BU KISIM ARTIK pdf_olustur fonksiyonunun DIŞINDA VE EN SOLDAN BAŞLAMALI:

if __name__ == "__main__":
    root = tk.Tk()
    YoklamaUygulamasi(root)
    root.mainloop()
