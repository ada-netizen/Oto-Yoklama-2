import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime, timedelta
import calendar
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sistem_motoru import SistemMotoru

UI_FONT = "Segoe UI"
YOLLAR = SistemMotoru.klasorleri_ve_yollari_hazirla()

PDF_KLASORU_VARSAYILAN = YOLLAR["PDF"]
YEDEK_KLASORU_VARSAYILAN = YOLLAR["YEDEK"]
MEB_LOGO_KLASORU = YOLLAR["MEB_LOGO"]
OKUL_LOGO_KLASORU = YOLLAR["OKUL_LOGO"]

class AltPencerelerMixin:
    def yardim_penceresi_ac(self):
        yardim_win = tk.Toplevel(self.root)
        yardim_win.title("Kullanım Kılavuzu")
        yardim_win.geometry("650x450")
        
        bg_col = "#1E293B" if self.is_dark_mode else "#F8FAFC"
        fg_col = "#F8FAFC" if self.is_dark_mode else "#0F172A"
        yardim_win.configure(bg=bg_col); yardim_win.grab_set()

        yardim_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 325
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 225
        yardim_win.geometry(f"+{x}+{y}")

        ust_frame = tk.Frame(yardim_win, bg="#1E3A8A", pady=15, padx=20)
        ust_frame.pack(fill=tk.X)
        tk.Label(ust_frame, text="📖 Nasıl Kullanılır?", font=(UI_FONT, 14, "bold"), bg="#1E3A8A", fg="white").pack(anchor=tk.W)

        notebook = ttk.Notebook(yardim_win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        sekme1 = tk.Frame(notebook, bg=bg_col, padx=15, pady=15)
        notebook.add(sekme1, text="1. Öğrenci Yükleme")
        m1 = ("Sisteme yeni öğrencileri dahil etmek veya mevcut listeyi güncellemek için:\n\n1. E-Okul sisteminden güncel 'Sınıf Listesi'ni Excel (xls, xlsx) formatında indirin.\n\n2. Üst menüde yer alan 'Öğrenci Yükle' butonuna tıklayarak indirdiğiniz dosyayı seçin.\n\n3. Sistem; mevcut öğrencileri korur, sadece yeni gelenleri ekler veya değişiklikleri (Nakil vb.) günceller.\n\n💡 Tekil öğrenci eklemek için menüdeki '➕ Yeni Öğrenci' butonunu da kullanabilirsiniz.")
        tk.Label(sekme1, text=m1, font=(UI_FONT, 10), bg=bg_col, fg=fg_col, justify=tk.LEFT, wraplength=580).pack(anchor=tk.NW)

        sekme2 = tk.Frame(notebook, bg=bg_col, padx=15, pady=15)
        notebook.add(sekme2, text="2. Devamsızlık Yükleme")
        m2 = ("Öğrencilerin güncel devamsızlık verilerini işlemek için:\n\n1. E-Okul'dan okulun genel veya sınıflar bazında 'Devamsızlık Listesi'ni Excel olarak indirin.\n\n2. 'Devamsızlık Yükle' butonuna basarak bu Excel'i sisteme okutun.\n\n3. Mükemmel Eşleşme: Sistem aynı devamsızlığı asla iki kez girmez! Her gün güvenle aynı listeyi tekrar tekrar yükleyebilirsiniz.\n\n💡 İpucu: Excel'de yazan 'Yarım' günleri sistem otomatik olarak '0.5' güne çevirerek hassas hesaplama yapar.")
        tk.Label(sekme2, text=m2, font=(UI_FONT, 10), bg=bg_col, fg=fg_col, justify=tk.LEFT, wraplength=580).pack(anchor=tk.NW)

        sekme3 = tk.Frame(notebook, bg=bg_col, padx=15, pady=15)
        notebook.add(sekme3, text="3. Çıktı Alma")
        m3 = ("Raporlama ve veli bildirimleri için iki güçlü seçeneğiniz var:\n\n• Veli Bildirim Formu (A5): Listeden bir öğrenci seçin. Sağ paneldeki takvimden günleri tıklayarak (veya Hızlı Seçim butonlarıyla) listeye alın. Ardından 'PDF ÇIKTISI AL' butonuna basın.\n\n• Toplu Excel/PDF Raporları: Üst menüden '📄 Raporlar' ekranını açın. Sınırı aşanları (10/20 gün), istediğiniz özel gün sayısını geçenleri (Örn: 6 gün ve üstü) veya belirli bir şubeye ait tüm listeyi tek tıklamayla alabilirsiniz.")
        tk.Label(sekme3, text=m3, font=(UI_FONT, 10), bg=bg_col, fg=fg_col, justify=tk.LEFT, wraplength=580).pack(anchor=tk.NW)

    def ayarlar_penceresi_ac(self):
        self.ayar_win = tk.Toplevel(self.root)
        self.ayar_win.title("Ayarlar ve Sistem Yönetimi")
        bg_col = "#1E293B" if self.is_dark_mode else "#F8FAFC"
        fg_col = "#F8FAFC" if self.is_dark_mode else "#0F172A"
        fg_sub = "#94A3B8" if self.is_dark_mode else "#64748B"
        self.ayar_win.configure(bg=bg_col); self.ayar_win.grab_set()

        ana_f = tk.Frame(self.ayar_win, bg=bg_col, padx=20, pady=20)
        ana_f.pack(fill=tk.BOTH, expand=True)

        # --- 1. KUTU: KURUMSAL KİMLİK ---
        kutu1 = tk.LabelFrame(ana_f, text=" Kurumsal Kimlik ", font=(UI_FONT, 10, "bold"), bg=bg_col, fg=fg_col, padx=10, pady=10)
        kutu1.pack(fill=tk.X, pady=5)

        tk.Label(kutu1, text="Okul Adı:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=0, column=0, padx=5, pady=8, sticky=tk.E)
        ent_okul = tk.Entry(kutu1, width=40, font=(UI_FONT, 10))
        ent_okul.insert(0, self.ayarlar.get("okul_adi", "Okul Adı"))
        ent_okul.grid(row=0, column=1, pady=8, sticky=tk.W)

        tk.Label(kutu1, text="MEB Logosu:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=1, column=0, padx=5, pady=8, sticky=tk.E)
        path_frame_meb = tk.Frame(kutu1, bg=bg_col); path_frame_meb.grid(row=1, column=1, pady=8, sticky=tk.W)
        m_yol_meb = self.ayarlar.get("meb_logosu", "")
        g_yol_meb = m_yol_meb if m_yol_meb else "Merkezde Yok"
        lbl_meb_yol = tk.Label(path_frame_meb, text=g_yol_meb if len(g_yol_meb)<=28 else "..."+g_yol_meb[-25:], width=22, anchor="w", fg="#F59E0B" if not self.is_dark_mode else "#FBBF24", bg=bg_col, font=(UI_FONT, 9, "bold"))
        lbl_meb_yol.pack(side=tk.LEFT)
        def sec_meb_logo():
            yol = filedialog.askopenfilename(title="MEB Logosu Seçin", filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg")])
            if yol:
                hedef_yol = os.path.join(MEB_LOGO_KLASORU, os.path.basename(yol))
                try:
                    shutil.copy(yol, hedef_yol)
                    self.ayarlar["meb_logosu"] = hedef_yol
                    lbl_meb_yol.config(text=hedef_yol if len(hedef_yol)<=28 else "..."+hedef_yol[-25:])
                except: self.bildirim_goster("Logo kopyalanamadı!", "hata")
        btn_sec_meb = tk.Button(path_frame_meb, text="Logo Seç", command=sec_meb_logo, padx=8)
        btn_sec_meb.pack(side=tk.LEFT, padx=10); self.style_button(btn_sec_meb, "#E2E8F0", "#334155", "#CBD5E1", font_size=9)

        tk.Label(kutu1, text="Okul Logosu:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=2, column=0, padx=5, pady=8, sticky=tk.E)
        path_frame_logo = tk.Frame(kutu1, bg=bg_col); path_frame_logo.grid(row=2, column=1, pady=8, sticky=tk.W)
        m_yol_logo = self.ayarlar.get("okul_logosu", "")
        g_yol_logo = m_yol_logo if m_yol_logo else "Merkezde Yok"
        lbl_logo_yol = tk.Label(path_frame_logo, text=g_yol_logo if len(g_yol_logo)<=28 else "..."+g_yol_logo[-25:], width=22, anchor="w", fg="#D946EF" if not self.is_dark_mode else "#E879F9", bg=bg_col, font=(UI_FONT, 9, "bold"))
        lbl_logo_yol.pack(side=tk.LEFT)
        def sec_logo():
            yol = filedialog.askopenfilename(title="Okul Logosu Seçin", filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg")])
            if yol:
                hedef_yol = os.path.join(OKUL_LOGO_KLASORU, os.path.basename(yol))
                try:
                    shutil.copy(yol, hedef_yol)
                    self.ayarlar["okul_logosu"] = hedef_yol
                    lbl_logo_yol.config(text=hedef_yol if len(hedef_yol)<=28 else "..."+hedef_yol[-25:])
                except: self.bildirim_goster("Logo kopyalanamadı!", "hata")
        btn_sec_logo = tk.Button(path_frame_logo, text="Logo Seç", command=sec_logo, padx=8)
        btn_sec_logo.pack(side=tk.LEFT, padx=10); self.style_button(btn_sec_logo, "#E2E8F0", "#334155", "#CBD5E1", font_size=9)

        # --- 2. KUTU: DOSYA YÖNETİMİ ---
        kutu2 = tk.LabelFrame(ana_f, text=" Dosya ve Çıktı Yönetimi ", font=(UI_FONT, 10, "bold"), bg=bg_col, fg=fg_col, padx=10, pady=10)
        kutu2.pack(fill=tk.X, pady=5)

        tk.Label(kutu2, text="PDF Kayıt Yeri:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=0, column=0, padx=5, pady=8, sticky=tk.E)
        path_frame = tk.Frame(kutu2, bg=bg_col); path_frame.grid(row=0, column=1, pady=8, sticky=tk.W)
        mevcut_yol = self.ayarlar.get("pdf_kayit_klasoru", PDF_KLASORU_VARSAYILAN)
        self.ayarlar["pdf_kayit_klasoru"] = mevcut_yol
        lbl_klasor_yol = tk.Label(path_frame, text=mevcut_yol if len(mevcut_yol)<=28 else "..."+mevcut_yol[-25:], width=22, anchor="w", fg="#2563EB" if not self.is_dark_mode else "#60A5FA", bg=bg_col, font=(UI_FONT, 9, "bold"))
        lbl_klasor_yol.pack(side=tk.LEFT)
        btn_klasor_sec = tk.Button(path_frame, text="Klasör Seç", command=lambda: lbl_klasor_yol.config(text=self.pdf_klasor_sec() or mevcut_yol), padx=8)
        btn_klasor_sec.pack(side=tk.LEFT, padx=10); self.style_button(btn_klasor_sec, "#E2E8F0", "#334155", "#CBD5E1", font_size=9)

        tk.Label(kutu2, text="Yedek Kayıt Yeri:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=1, column=0, padx=5, pady=8, sticky=tk.E)
        path_frame_yedek = tk.Frame(kutu2, bg=bg_col); path_frame_yedek.grid(row=1, column=1, pady=8, sticky=tk.W)
        m_yol_yedek = self.ayarlar.get("yedek_kayit_klasoru", YEDEK_KLASORU_VARSAYILAN)
        self.ayarlar["yedek_kayit_klasoru"] = m_yol_yedek
        lbl_ky_yol = tk.Label(path_frame_yedek, text=m_yol_yedek if len(m_yol_yedek)<=28 else "..."+m_yol_yedek[-25:], width=22, anchor="w", fg="#10B981" if not self.is_dark_mode else "#34D399", bg=bg_col, font=(UI_FONT, 9, "bold"))
        lbl_ky_yol.pack(side=tk.LEFT)
        def sec_yedek():
            yol = filedialog.askdirectory(title="Yedekleme Klasörü Seçin")
            if yol:
                self.ayarlar["yedek_kayit_klasoru"] = yol
                lbl_ky_yol.config(text=yol if len(yol)<=28 else "..."+yol[-25:])
        btn_sec_yedek = tk.Button(path_frame_yedek, text="Klasör Seç", command=sec_yedek, padx=8)
        btn_sec_yedek.pack(side=tk.LEFT, padx=10); self.style_button(btn_sec_yedek, "#E2E8F0", "#334155", "#CBD5E1", font_size=9)

        # --- 3. KUTU: YEDEKLEME MOTORU ---
        kutu3 = tk.LabelFrame(ana_f, text=" Yedekleme Motoru ", font=(UI_FONT, 10, "bold"), bg=bg_col, fg=fg_col, padx=10, pady=10)
        kutu3.pack(fill=tk.X, pady=5)

        tk.Label(kutu3, text="Yedekleme Sıklığı:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=0, column=0, padx=5, pady=8, sticky=tk.E)
        f_siklik = tk.Frame(kutu3, bg=bg_col); f_siklik.grid(row=0, column=1, pady=8, sticky=tk.W)
        combo_siklik = ttk.Combobox(f_siklik, values=["Her Gün", "Özel Gün", "Haftada 1", "Ayda 1"], state="readonly", width=10)
        combo_siklik.set(self.ayarlar.get("yedek_sikligi", "Her Gün")); combo_siklik.pack(side=tk.LEFT)
        
        lbl_gun = tk.Label(f_siklik, text="Gün sayısı:", bg=bg_col, fg=fg_col, font=(UI_FONT, 9))
        ent_gun = tk.Entry(f_siklik, width=4)
        ent_gun.insert(0, self.ayarlar.get("yedek_gun_sayisi", "3"))
        
        def siklik_degisim(e):
            if combo_siklik.get() == "Özel Gün":
                lbl_gun.pack(side=tk.LEFT, padx=(10,2)); ent_gun.pack(side=tk.LEFT)
            else:
                lbl_gun.pack_forget(); ent_gun.pack_forget()
        combo_siklik.bind("<<ComboboxSelected>>", siklik_degisim); siklik_degisim(None)

        tk.Label(kutu3, text="Yedekleme Saati:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=1, column=0, padx=5, pady=8, sticky=tk.E)
        ent_saat = tk.Entry(kutu3, width=8, font=(UI_FONT, 10))
        ent_saat.insert(0, self.ayarlar.get("yedek_saati", "17:00"))
        ent_saat.grid(row=1, column=1, pady=8, sticky=tk.W)
        tk.Label(kutu3, text="(Örn: 15:30)", bg=bg_col, fg=fg_sub, font=(UI_FONT, 8)).grid(row=1, column=1, padx=(65,0), sticky=tk.W)

        tk.Label(kutu3, text="Eski Yedekleri Sil:", bg=bg_col, fg=fg_col, font=(UI_FONT, 10)).grid(row=2, column=0, padx=5, pady=8, sticky=tk.E)
        combo_silme = ttk.Combobox(kutu3, values=["1 Hafta Sonra", "1 Ay Sonra", "3 Ay Sonra", "6 Ay Sonra", "1 Yıl Sonra", "Asla Silme"], state="readonly", width=18)
        combo_silme.set(self.ayarlar.get("yedek_silme_suresi", "1 Ay Sonra"))
        combo_silme.grid(row=2, column=1, pady=8, sticky=tk.W)

        # --- BUTONLAR ---
        btn_f = tk.Frame(ana_f, bg=bg_col)
        btn_f.pack(pady=10, fill=tk.X)
        btn_f.columnconfigure(0, weight=1); btn_f.columnconfigure(1, weight=1)

        def kaydet_kapat():
            self.ayarlar.update({
                "okul_adi": ent_okul.get(), "yedek_sikligi": combo_siklik.get(),
                "yedek_gun_sayisi": ent_gun.get(), "yedek_saati": ent_saat.get(),
                "yedek_silme_suresi": combo_silme.get()
            })
            self.ayarlari_kaydet()
            self.bildirim_goster("Sistem ayarları güncellendi.", "bilgi")
            self.ayar_win.destroy()

        btn_save = tk.Button(btn_f, text="Değişiklikleri Kaydet", command=kaydet_kapat, pady=8)
        btn_save.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.style_button(btn_save, "#38BB94", "#FFFFFF", "#00897B", font_size=11)
        
        btn_simdi_yedek = tk.Button(btn_f, text="💾 Şimdi Yedek Al", command=self.manuel_yedek_al, pady=8)
        btn_simdi_yedek.grid(row=1, column=0, sticky="ew", padx=(0,4), pady=(0, 8))
        self.style_button(btn_simdi_yedek, "#8B5CF6", "#FFFFFF", "#7C3AED", font_size=10)

        btn_yedek = tk.Button(btn_f, text="🔄 Yedeği Geri Yükle", command=self.yedek_yukle, pady=8)
        btn_yedek.grid(row=1, column=1, sticky="ew", padx=(4,0), pady=(0, 8))
        self.style_button(btn_yedek, "#3B82F6", "#FFFFFF", "#2563EB", font_size=10)

        btn_sifirla = tk.Button(btn_f, text="🗑️ Tüm Veritabanını Sıfırla", command=self.veritabani_sifirla, pady=8)
        btn_sifirla.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.style_button(btn_sifirla, "#FEE2E2", "#B91C1C", "#FCA5A5", font_size=10)

        self.ayar_win.update_idletasks()
        g, y = max(550, self.ayar_win.winfo_reqwidth()), self.ayar_win.winfo_reqheight() + 10 
        x, y_p = self.root.winfo_x() + (self.root.winfo_width() // 2) - (g // 2), self.root.winfo_y() + (self.root.winfo_height() // 2) - (y // 2)
        self.ayar_win.geometry(f"{g}x{y}+{x}+{y_p}")     

    def rapor_penceresi_ac(self):
        self.rapor_win = tk.Toplevel(self.root)
        self.rapor_win.title("Raporlar")
        bg_col = "#1E293B" if self.is_dark_mode else "#F8FAFC"
        fg_col = "#F8FAFC" if self.is_dark_mode else "#0F172A"
        self.rapor_win.configure(bg=bg_col); self.rapor_win.grab_set()

        card = tk.Frame(self.rapor_win, bg=bg_col, highlightthickness=1, padx=20, pady=20)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        subeler_set = set()
        for ogr in self.ogrenci_listesi:
            if ogr['sube']: subeler_set.add(self.kisa_sube_adi(ogr['sube']))
        sube_listesi = ["Seç"] + sorted(list(subeler_set))

        def satir_ekle(parent, metin, komut_pdf, komut_xls):
            frm = tk.Frame(parent, bg=bg_col)
            frm.pack(fill=tk.X, pady=10)
            tk.Label(frm, text=metin, font=(UI_FONT, 11, "bold"), bg=bg_col, fg=fg_col).pack(side=tk.LEFT)
            
            if komut_xls:
                btn_x = tk.Button(frm, text="Excel", command=komut_xls, width=7, pady=4)
                btn_x.pack(side=tk.RIGHT, padx=(5, 0))
                self.style_button(btn_x, "#10B981", "#FFFFFF", "#059669", font_size=10)
            if komut_pdf:
                btn_p = tk.Button(frm, text="PDF", command=komut_pdf, width=7, pady=4)
                btn_p.pack(side=tk.RIGHT, padx=(5, 0))
                self.style_button(btn_p, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)

        def dinamik_rapor_tetikle(tur, secim_widget, format_tipi):
            deger = secim_widget.get()
            if deger in ["Seçiniz...", "Seç", ""] or not deger:
                self.bildirim_goster("Lütfen rapor almadan önce listeden bir seçim yapınız!", "hata")
                return
            self.toplu_rapor_al(tur, format_tipi, self.rapor_win, ozel_deger=deger)

        # 1. ESKİ RAPORLAR
        satir_ekle(card, "Özürsüz Sınırını Aşanlar", 
                   lambda: self.toplu_rapor_al("ozursuz", "pdf", self.rapor_win), 
                   lambda: self.toplu_rapor_al("ozursuz", "excel", self.rapor_win))
                   
        satir_ekle(card, "Özürlü Sınırını Aşanlar", 
                   lambda: self.toplu_rapor_al("ozurlu", "pdf", self.rapor_win), 
                   lambda: self.toplu_rapor_al("ozurlu", "excel", self.rapor_win))

        # 2. DİNAMİK GÜN SINIRI SEÇİMİ
        frm_gun = tk.Frame(card, bg=bg_col)
        frm_gun.pack(fill=tk.X, pady=10)
        tk.Label(frm_gun, text="Özürsüz Devamsızlığı", font=(UI_FONT, 11, "bold"), bg=bg_col, fg=fg_col).pack(side=tk.LEFT)
        
        combo_gun = ttk.Combobox(frm_gun, values=["Seç", "5 Gün", "6 Gün", "7 Gün", "8 Gün", "9 Gün"], state="readonly", width=4, font=(UI_FONT, 10, "bold"), justify="center")
        combo_gun.set("Seç")
        combo_gun.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frm_gun, text="ve Üstü Olan Öğrenci Listesi", font=(UI_FONT, 11, "bold"), bg=bg_col, fg=fg_col).pack(side=tk.LEFT)
        
        btn_x_gun = tk.Button(frm_gun, text="Excel", command=lambda: dinamik_rapor_tetikle("gun_siniri", combo_gun, "excel"), width=7, pady=4)
        btn_x_gun.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_x_gun, "#10B981", "#FFFFFF", "#059669", font_size=10)
        
        btn_p_gun = tk.Button(frm_gun, text="PDF", command=lambda: dinamik_rapor_tetikle("gun_siniri", combo_gun, "pdf"), width=7, pady=4)
        btn_p_gun.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_p_gun, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)

        # 3. ŞUBEYE GÖRE ÖZÜRSÜZ LİSTESİ
        frm_sube = tk.Frame(card, bg=bg_col)
        frm_sube.pack(fill=tk.X, pady=10)
        
        combo_sube = ttk.Combobox(frm_sube, values=sube_listesi, state="readonly", width= 6, font=(UI_FONT, 10))
        combo_sube.set("Seç")
        combo_sube.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(frm_sube, text="Şubesi Toplam Özürsüz Devamsızlık Listesi", font=(UI_FONT, 11, "bold"), bg=bg_col, fg=fg_col).pack(side=tk.LEFT)
              
        btn_x_sube = tk.Button(frm_sube, text="Excel", command=lambda: dinamik_rapor_tetikle("sube_bazli", combo_sube, "excel"), width=7, pady=4)
        btn_x_sube.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_x_sube, "#10B981", "#FFFFFF", "#059669", font_size=10)

        btn_p_sube = tk.Button(frm_sube, text="PDF", command=lambda: dinamik_rapor_tetikle("sube_bazli", combo_sube, "pdf"), width=7, pady=4)
        btn_p_sube.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_p_sube, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)
        
        # --- YENİ EKLENEN KISIM: 4. BELİRLİ TARİHE GÖRE ÖZÜRSÜZ LİSTESİ ---
        frm_tarih = tk.Frame(card, bg=bg_col)
        frm_tarih.pack(fill=tk.X, pady=10)
        
        try:
            from tkcalendar import DateEntry
            cal_tarih = DateEntry(frm_tarih, width=10, date_pattern='dd/mm/yyyy', locale='tr_TR', font=(UI_FONT, 10))
        except:
            cal_tarih = tk.Entry(frm_tarih, width=12, font=(UI_FONT, 10), justify="center")
            cal_tarih.insert(0, datetime.now().strftime("%d/%m/%Y"))
        cal_tarih.pack(side=tk.LEFT, padx=(0, 10)) # Başa aldık
        
        tk.Label(frm_tarih, text="Tarihinde Özürsüz Devamsızlık Yapanlar", font=(UI_FONT, 11, "bold"), bg=bg_col, fg=fg_col).pack(side=tk.LEFT)
        
        btn_p_tarih = tk.Button(frm_tarih, text="PDF", command=lambda: dinamik_rapor_tetikle("tarih_bazli", cal_tarih, "pdf"), width=7, pady=4)
        btn_p_tarih.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_p_tarih, "#EF4444", "#FFFFFF", "#DC2626", font_size=10)
        
        btn_x_tarih = tk.Button(frm_tarih, text="Excel", command=lambda: dinamik_rapor_tetikle("tarih_bazli", cal_tarih, "excel"), width=7, pady=4)
        btn_x_tarih.pack(side=tk.RIGHT, padx=(5, 0))
        self.style_button(btn_x_tarih, "#10B981", "#FFFFFF", "#059669", font_size=10)
        # -----------------------------------------------------------------

        self.rapor_win.update_idletasks()
        genislik = max(650, self.rapor_win.winfo_reqwidth())
        yukseklik = self.rapor_win.winfo_reqheight() + 10 
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (genislik // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (yukseklik // 2)
        self.rapor_win.geometry(f"{genislik}x{yukseklik}+{x}+{y}")
        
    def toplu_rapor_al(self, tur, format_tipi, pencere=None, ozel_deger=None):
        if not self.ogrenci_listesi:
            self.bildirim_goster("Sistemde öğrenci bulunmuyor.", "hata")
            return
            
        # Tarih bazlı rapor için hedef tarihi bilgisayarın anlayacağı formata çeviriyoruz
        hedef_tarih_obj = None
        if tur == "tarih_bazli":
            try:
                ht_d, ht_m, ht_y = map(int, ozel_deger.split('/'))
                hedef_tarih_obj = datetime(ht_y, ht_m, ht_d)
            except:
                self.bildirim_goster("Tarih formatı hatalı! (GG/AA/YYYY olmalı)", "hata")
                return

        veri = []
        for ogr in self.ogrenci_listesi:
            ozsz, ozrl = self.hesapla_devamsizlik(ogr['no'])
            gosterilen_sube = self.kisa_sube_adi(ogr['sube'])
            
            # --- FİLTRELEME MOTORLARI ---
            if tur == "ozursuz" and ozsz < 10: continue
            if tur == "ozurlu" and ozrl < 20: continue
            if tur == "gun_siniri" and ozsz < int(ozel_deger): continue
            if tur == "sube_bazli" and gosterilen_sube != ozel_deger: continue
            
            # YENİ: TARİH BAZLI FİLTRE MOTORU
            if tur == "tarih_bazli":
                tarihte_yok = False
                dev_turu = ""
                # Çocuğun tüm devamsızlıklarını tarar
                for dev in self.devamsizlik_listesi:
                    if str(dev['no']).strip() == str(ogr['no']).strip() and dev['tur'].upper() in ["D", "ÖY", "SY"]:
                        try:
                            gun_mik = float(self.temiz_sure(dev['gun']))
                            tam_g = int(gun_mik) if gun_mik >= 1 else 1
                            bd, bm, by = map(int, self.tarih_formatla(dev['tarih']).split('/'))
                            bas_tarih = datetime(by, bm, bd)
                            
                            # Devamsızlık kaç gün sürdüyse (örn: 3 gün), o günleri tek tek sayıp aranan tarihe denk gelmiş mi bakar
                            for i in range(tam_g):
                                g_t = bas_tarih + timedelta(days=i)
                                if g_t.weekday() < 5 and g_t.date() == hedef_tarih_obj.date():
                                    tarihte_yok = True
                                    dev_turu = dev['tur'].upper()
                                    break
                            if tarihte_yok: break
                        except: pass
                
                if not tarihte_yok: continue
                # Tarih tablosuna eklenecek veri (Son kolon Toplam Gün değil, Devamsızlık Türü olur)
                veri.append([gosterilen_sube, ogr['no'], ogr['ad_soyad'], dev_turu])
            else:
                # Diğer tüm raporlar için eklenecek standart veri
                veri.append([gosterilen_sube, ogr['no'], ogr['ad_soyad'], ozsz])

        if not veri:
            self.bildirim_goster("Bu kritere uygun öğrenci bulunamadı.", "hata")
            return

        # --- SIRALAMA İŞLEMİ ---
        if tur == "tarih_bazli":
            # Tarih raporunda sınıfa (9-10-11-12) ve numaraya göre sıralama daha mantıklıdır
            def siralama_anahtari(x):
                import re
                r = re.findall(r'\d+', str(x[0]))
                sinif_no = int(r[0]) if r else 99
                return (sinif_no, x[0], int(x[1]) if str(x[1]).isdigit() else str(x[1]))
            veri.sort(key=siralama_anahtari)
        else:
            # Diğer raporlarda çok devamsızlık yapandan aza doğru sıralanır
            veri.sort(key=lambda x: x[3], reverse=True)

        # BAŞLIKLAR VE KOLON İSİMLERİ
        if tur == "ozursuz": baslik = "Özürsüz Devamsızlık Sınırını Aşan Öğrenciler (10+ Gün)"
        elif tur == "ozurlu": baslik = "Özürlü Devamsızlık Sınırını Aşan Öğrenciler (20+ Gün)"
        elif tur == "gun_siniri": baslik = f"Özürsüz Devamsızlığı {ozel_deger} Gün ve Üstü Olan Öğrenciler"
        elif tur == "sube_bazli": baslik = f"{ozel_deger} Şubesi Özürsüz Devamsızlık Listesi"
        elif tur == "tarih_bazli": baslik = f"{ozel_deger} Tarihli Özürsüz Devamsızlık Listesi"

        if tur == "tarih_bazli":
            excel_kolonlar = ["Sınıf/Şube", "Numara", "Ad Soyad", "Devamsızlık Türü"]
            pdf_kolon4 = "Tür"
        else:
            excel_kolonlar = ["Sınıf/Şube", "Numara", "Ad Soyad", "Özürsüz Toplam (Gün)"]
            pdf_kolon4 = "Özürsüz (Gün)"

        import threading
        import re
        dosya_adi_temiz = re.sub(r'[\\/*?:"<>|]', "", baslik).replace(" ", "_")
        bugun_str = datetime.now().strftime("%d_%m_%Y")
        otomatik_isim = f"{dosya_adi_temiz}_{bugun_str}"

        if format_tipi == "excel":
            yol = filedialog.asksaveasfilename(
                initialfile=f"{otomatik_isim}.xlsx", 
                defaultextension=".xlsx", 
                filetypes=[("Excel", "*.xlsx")], 
                title="Excel Olarak Kaydet"
            )
            if not yol: return
            
            win = self.goster_yukleme_penceresi("Excel Hazırlanıyor...")
            def islem_excel():
                try:
                    import pandas as pd
                    df = pd.DataFrame(veri, columns=excel_kolonlar)
                    df.to_excel(yol, index=False)
                    self.root.after(0, lambda: self.rapor_tamam(win, yol, pencere, "Excel raporu başarıyla oluşturuldu."))
                except Exception as e:
                    self.root.after(0, lambda: self.hata_goster(win, f"Excel kaydedilemedi:\n{e}"))
            threading.Thread(target=islem_excel, daemon=True).start()
        
        elif format_tipi == "pdf":
            yol = filedialog.asksaveasfilename(
                initialfile=f"{otomatik_isim}.pdf", 
                defaultextension=".pdf", 
                filetypes=[("PDF", "*.pdf")], 
                title="PDF Olarak Kaydet"
            )
            if not yol: return
            
            win = self.goster_yukleme_penceresi("PDF Hazırlanıyor...")
            def islem_pdf():
                try:
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    c = canvas.Canvas(yol, pagesize=A4)
                    w, h = A4
                    c.setFont(self.pdf_font_bold if hasattr(self, 'pdf_font_bold') else self.pdf_font, 14)
                    c.drawCentredString(w/2, h - 50, self.tr_karakter_duzelt(baslik))
                    
                    y_pos = h - 80
                    c.setFont(self.pdf_font_bold if hasattr(self, 'pdf_font_bold') else self.pdf_font, 10)
                    
                    # PDF BAŞLIKLARI DİNAMİK YAPILDI
                    c.drawString(50, y_pos, self.tr_karakter_duzelt("Sınıf/Şube"))
                    c.drawString(130, y_pos, "No")
                    c.drawString(180, y_pos, "Ad Soyad")
                    c.drawString(450, y_pos, self.tr_karakter_duzelt(pdf_kolon4))
                        
                    c.line(40, y_pos - 5, w - 40, y_pos - 5)
                    
                    y_pos -= 20
                    c.setFont(self.pdf_font, 10) 
                    
                    for satir in veri:
                        if y_pos < 50:
                            c.showPage(); c.setFont(self.pdf_font, 10); y_pos = h - 50
                        
                        c.drawString(50, y_pos, self.tr_karakter_duzelt(str(satir[0])))
                        c.drawString(130, y_pos, str(satir[1]))
                        c.drawString(180, y_pos, self.tr_karakter_duzelt(str(satir[2])))
                        c.drawString(450, y_pos, str(satir[3]))
                        y_pos -= 15
                    
                    c.save()
                    self.root.after(0, lambda: self.rapor_tamam(win, yol, pencere, "PDF raporu başarıyla oluşturuldu."))
                except Exception as e: 
                    self.root.after(0, lambda: self.hata_goster(win, f"PDF oluşturulamadı:\n{e}"))
                    
            threading.Thread(target=islem_pdf, daemon=True).start()

    def rapor_tamam(self, win, yol, pencere, mesaj):
        """Asenkron işlem bittiğinde yükleme penceresini kapatır ve dosyayı açar."""
        win.destroy()
        self.bildirim_goster(mesaj, "bilgi")
        if os.name == 'nt': os.startfile(yol)
        if pencere: pencere.destroy()

    def ogrenci_cift_tiklandi(self, event):
        if not self.secili_ogrenci: return
        
        yillik_win = tk.Toplevel(self.root)
        yillik_win.title(f"Yıllık Devamsızlık Karnesi - {self.secili_ogrenci['ad_soyad']}")
        
        # PENCERE BOYUTU EN ALT KISIMDA DİNAMİK OLARAK HESAPLANACAK
        
        bg_main = "#0F172A" if self.is_dark_mode else "#F1F5F9"
        bg_card = "#1E293B" if self.is_dark_mode else "#FFFFFF"
        fg_main = "#F8FAFC" if self.is_dark_mode else "#1E293B"
        fg_sub = "#94A3B8" if self.is_dark_mode else "#64748B"
        border_col = "#334155" if self.is_dark_mode else "#CBD5E1"
        header_bg = "#1E3A8A" if self.is_dark_mode else "#1E3A8A" 
        
        yillik_win.configure(bg=bg_main)
        
        ust_frame = tk.Frame(yillik_win, bg=header_bg, pady=15, padx=20)
        ust_frame.pack(fill=tk.X)
        tk.Label(ust_frame, text="Özürlü - Özürsüz Devamsızlık Bilgisi", font=(UI_FONT, 14, "bold"), bg=header_bg, fg="white").pack(anchor=tk.W)
        
        tablo_frame = tk.Frame(yillik_win, bg=bg_card, highlightbackground=border_col, highlightthickness=1, padx=10, pady=10)
        tablo_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        for i in range(32): tablo_frame.columnconfigure(i, weight=1)
        
        aylar = ["Eylül", "Ekim", "Kasım", "Aralık", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran"]
        ay_numaralari = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
        
        cells = {}
        row_headers = {}
        col_headers = {}

        renk_haritasi = {
            "D": "#DC2626", "ÖY": "#EF4444", "SY": "#F87171", "G": "#EA580C",
            "İ": "#EAB308", "S": "#F59E0B", "R": "#D97706", "M": "#92400E",
            "N": "#3B82F6", "F": "#6366F1", "SV": "#8B5CF6"
        }

        # --- YENİ EFEKT MOTORU ---
        def hover_enter(r, c, tur=None):
            if tur: 
                # ALT PANEL EFEKTİ: Sadece o türdeki harfleri parlat, diğer her şeyi karart
                for (row, col), data in cells.items():
                    if data['is_abs']:
                        if data['tur'] == tur:
                            data['lbl'].config(bg=data['orj_bg'], fg="#FFFFFF")
                        else:
                            data['lbl'].config(bg=bg_card, fg=border_col)
                    elif data['is_valid']:
                        data['lbl'].config(bg=bg_card)
            else:
                # TABLO HÜCRESİ EFEKTİ: Hedefe giden yolu çiz, yolda olmayan HER ŞEYİ karart
                target_bg = "#CBD5E1" if not self.is_dark_mode else "#475569"
                target_fg = "#0F172A" if not self.is_dark_mode else "#F8FAFC"
                path_bg = "#E2E8F0" if not self.is_dark_mode else "#334155"
                border_hl = "#38BB94" 
                
                for (row, col), data in cells.items():
                    # Hücre hedefe giden yolda mı?
                    is_path = (row == r and col <= c) or (col == c and row <= r)
                    
                    if is_path:
                        if row == r and col == c: # Tıklanan hedefin tam üstü
                            data['lbl'].config(bg=data['orj_bg'], fg="#FFFFFF")
                        else: # Yolu oluşturan (yatay ve dikey) hücreler
                            if data['is_valid'] and not data['is_abs']:
                                data['lbl'].config(bg=path_bg, fg=target_fg)
                            elif data['is_abs']:
                                data['lbl'].config(bg=data['orj_bg'], fg="#FFFFFF")
                    else:
                        # Yolda OLMAYAN, tamamen alakasız hücreleri (dolu/boş) karart
                        if data['is_abs']:
                            data['lbl'].config(bg=bg_card, fg=border_col)
                        elif data['is_valid']:
                            data['lbl'].config(bg=bg_card)
                            
                if r and r in row_headers: row_headers[r].config(highlightbackground=border_hl)
                if c and c in col_headers: col_headers[c].config(highlightbackground=border_hl)

        def hover_leave(*args):
            # Fare çekilince istisnasız tüm hücreleri orijinal (renkli) haline geri döndür
            for (row, col), data in cells.items():
                if data['is_valid']:
                    data['lbl'].config(bg=data['orj_bg'], fg=data['orj_fg'])
                    
            for rh in row_headers.values(): rh.config(highlightbackground=border_col)
            for ch in col_headers.values(): ch.config(highlightbackground=header_bg)

        # --- TABLO BAŞLIKLARI ---
        tk.Label(tablo_frame, text="Aylar", bg=header_bg, fg="white", font=(UI_FONT, 9, "bold")).grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        for i in range(1, 32):
            lbl_col = tk.Label(tablo_frame, text=str(i), bg=header_bg, fg="white", font=(UI_FONT, 9, "bold"), highlightthickness=2, highlightbackground=header_bg)
            lbl_col.grid(row=0, column=i, padx=1, pady=1, sticky="nsew")
            col_headers[i] = lbl_col
            
        ogr_no_kati = str(self.secili_ogrenci['no']).strip()
        dev_map = {} 
        
        detay_ozursuz = {}
        detay_ozurlu = {}
        detay_diger = {}
        
        # --- EKLENEN HAFTA SONU HAFIZALARI ---
        hs_ozursuz = {}
        hs_ozurlu = {}
        hs_diger = {}
        
        ozsz_toplam_net = 0.0
        ozrl_toplam_net = 0.0
        diger_toplam_net = 0.0
        
        g_sayisi = 0 
        
        for dev in self.devamsizlik_listesi + self.gecici_devamsizliklar:
            if str(dev['no']).strip() == ogr_no_kati:
                tur = dev['tur'].upper()
                
                try: gun_miktari = float(self.temiz_sure(dev['gun']))
                except: gun_miktari = 0.0
                
                tam_gun = int(gun_miktari) if gun_miktari >= 1 else 1
                
                hs_miktari = 0.0
                hi_miktari = 0.0

                try:
                    d, m, y = map(int, self.tarih_formatla(dev['tarih']).split('/'))
                    baslangic_tarihi = datetime(y, m, d)
                    
                    # 1. GÜNLERİ TAKVİME YAYMA (Sadece Hafta İçi)
                    for i in range(tam_gun):
                        g_tarih = baslangic_tarihi + timedelta(days=i)
                        if g_tarih.weekday() < 5: 
                            dev_map[(g_tarih.month, g_tarih.day)] = tur
                            
                    # 2. HAFTA SONU / HAFTA İÇİ AYIRIMI (Mükemmel Hesaplama)
                    if gun_miktari <= 1:
                        if baslangic_tarihi.weekday() >= 5:
                            hs_miktari = gun_miktari
                        else:
                            hi_miktari = gun_miktari
                    else:
                        for i in range(tam_gun):
                            g_tarih = baslangic_tarihi + timedelta(days=i)
                            if g_tarih.weekday() >= 5:
                                hs_miktari += 1
                            else:
                                hi_miktari += 1
                except: 
                    hi_miktari = gun_miktari # Hata olursa varsayılan olarak hepsini hafta içi say
                
                # İŞLEMLER (Net toplamlar ve Hafta sonları ayrı kaydediliyor)
                if tur in ["D", "ÖY", "SY"]: 
                    detay_ozursuz[tur] = detay_ozursuz.get(tur, 0.0) + gun_miktari
                    hs_ozursuz[tur] = hs_ozursuz.get(tur, 0.0) + hs_miktari
                    ozsz_toplam_net += hi_miktari
                elif tur == "G":
                    g_sayisi += 1 
                elif tur in ["N", "F", "SV"]: 
                    detay_diger[tur] = detay_diger.get(tur, 0.0) + gun_miktari
                    hs_diger[tur] = hs_diger.get(tur, 0.0) + hs_miktari
                    diger_toplam_net += hi_miktari
                else: 
                    detay_ozurlu[tur] = detay_ozurlu.get(tur, 0.0) + gun_miktari
                    hs_ozurlu[tur] = hs_ozurlu.get(tur, 0.0) + hs_miktari
                    ozrl_toplam_net += hi_miktari

        if g_sayisi > 0:
            g_gun_karsiligi = (g_sayisi // 5) * 0.5
            detay_ozursuz[f"G ({g_sayisi})"] = g_gun_karsiligi 
            ozsz_toplam_net += g_gun_karsiligi

        # --- TABLO İÇERİĞİ ---
        for row_idx, (ay_ad, ay_no) in enumerate(zip(aylar, ay_numaralari), start=1):
            lbl_row = tk.Label(tablo_frame, text=ay_ad, bg=border_col, fg=fg_main, font=(UI_FONT, 9, "bold"), highlightthickness=2, highlightbackground=border_col)
            lbl_row.grid(row=row_idx, column=0, padx=1, pady=1, sticky="nsew")
            row_headers[row_idx] = lbl_row
            
            for gun in range(1, 32):
                is_valid = True
                is_weekend = False
                
                try: 
                    y = self.cal_year if ay_no < 8 else self.cal_year - 1
                    dt = datetime(y, ay_no, gun)
                    if dt.weekday() >= 5: is_weekend = True 
                except ValueError:
                    is_valid = False

                if not is_valid:
                    cell_bg = "#D1D5DB" if not self.is_dark_mode else "#0B1120"
                elif is_weekend:
                    cell_bg = "#D1D5DB" if not self.is_dark_mode else "#0B1120" 
                else:
                    cell_bg = "#F1F5F9" if not self.is_dark_mode else "#1E293B" 
                    
                cell_text = ""
                cell_fg = fg_main
                is_abs = False
                
                if (ay_no, gun) in dev_map:
                    is_abs = True
                    cell_text = dev_map[(ay_no, gun)]
                    cell_bg = renk_haritasi.get(cell_text, "#64748B")
                    cell_fg = "#FFFFFF"

                lbl = tk.Label(tablo_frame, text=cell_text, bg=cell_bg, fg=cell_fg, font=(UI_FONT, 9, "bold"))
                lbl.grid(row=row_idx, column=gun, padx=1, pady=1, sticky="nsew")
                
                cells[(row_idx, gun)] = {'lbl': lbl, 'orj_bg': cell_bg, 'orj_fg': cell_fg, 'is_valid': is_valid, 'is_abs': is_abs, 'tur': cell_text}
                
                # EFEKT SADECE DEVAMSIZLIK İŞLENEN (DOLU) HÜCRELERDE ÇALIŞIR
                if is_abs:
                    lbl.bind("<Enter>", lambda e, r=row_idx, c=gun: hover_enter(r, c))
                    lbl.bind("<Leave>", hover_leave)
                
        ozet_frame = tk.Frame(yillik_win, bg=bg_main)
        ozet_frame.pack(fill=tk.X, padx=20, pady=(0,20))

        # --- ÖZET KUTUSU MİMARİSİ (Hafta Sonu Matematiği Eklendi) ---
        def ozet_kutusu_olustur(baslik, detay_dict, hs_dict, toplam_deger, vurgu_rengi):
            kutu = tk.Frame(ozet_frame, bg=bg_card, highlightthickness=1, highlightbackground=border_col)
            kutu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            tk.Label(kutu, text=baslik, bg=header_bg, fg="white", font=(UI_FONT, 11, "bold"), pady=5).pack(side=tk.TOP, fill=tk.X)
            
            toplam_str = int(toplam_deger) if float(toplam_deger).is_integer() else toplam_deger
            tk.Label(kutu, text=f"Toplam: {toplam_str} Gün", bg=bg_card, fg=vurgu_rengi, font=(UI_FONT, 12, "bold"), pady=10).pack(side=tk.BOTTOM, fill=tk.X)

            orta_tasiyici = tk.Frame(kutu, bg=bg_card)
            orta_tasiyici.pack(side=tk.TOP, expand=True)

            ic_liste = tk.Frame(orta_tasiyici, bg=bg_card)
            ic_liste.pack(anchor=tk.CENTER) 
            
            if detay_dict:
                for tur, gun in detay_dict.items():
                    hs_gun = hs_dict.get(tur, 0.0) if hs_dict else 0.0
                    
                    gun_str = int(gun) if float(gun).is_integer() else gun
                    hs_str = int(hs_gun) if float(hs_gun).is_integer() else hs_gun
                    
                    row_f = tk.Frame(ic_liste, bg=bg_card)
                    row_f.pack(anchor=tk.W, fill=tk.X, pady=2)
                    
                    saf_tur = tur.split(" ")[0] if "G (" in tur else tur
                    tur_yazi_rengi = renk_haritasi.get(saf_tur, fg_sub)
                    
                    lbl_tur = tk.Label(row_f, text=f"{tur} :", bg=bg_card, fg=tur_yazi_rengi, font=(UI_FONT, 10, "bold"), cursor="hand2")
                    lbl_tur.pack(side=tk.LEFT)
                    
                    # HAFTA SONU İSE PARANTEZ İÇİNDE GÖSTER
                    if hs_gun > 0:
                        metin = f"{gun_str} Gün ({hs_str} Gün Hafta Sonu)"
                    else:
                        metin = f"{gun_str} Gün"
                        
                    lbl_gun = tk.Label(row_f, text=metin, bg=bg_card, fg=fg_sub, font=(UI_FONT, 10), cursor="hand2")
                    lbl_gun.pack(side=tk.LEFT, padx=(5,0))
                    
                    # Sadece alt paneldeki yazılara özel hedef parlatma efekti
                    for w in (row_f, lbl_tur, lbl_gun):
                        w.bind("<Enter>", lambda e, t=saf_tur: hover_enter(None, None, t))
                        w.bind("<Leave>", hover_leave)
            else:
                tk.Label(ic_liste, text="Kayıt Yok", bg=bg_card, fg=fg_sub, font=(UI_FONT, 10)).pack(anchor=tk.CENTER, pady=2)

        ozet_kutusu_olustur("Özürlü Devamsızlık", detay_ozurlu, hs_ozurlu, ozrl_toplam_net, fg_main)
        ozet_kutusu_olustur("Özürsüz Devamsızlık", detay_ozursuz, hs_ozursuz, ozsz_toplam_net, "#DC2626" if ozsz_toplam_net>=10 else fg_main)
        ozet_kutusu_olustur("Diğer Devamsızlık", detay_diger, hs_diger, diger_toplam_net, fg_main)

        # --- DİNAMİK PENCERE BOYUTLANDIRMA VE ORTALAMA ---
        yillik_win.update_idletasks()
        gerekli_genislik = 1350
        gerekli_yukseklik = yillik_win.winfo_reqheight() + 20 
        
        son_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (gerekli_genislik // 2)
        son_y = max(0, self.root.winfo_y() + (self.root.winfo_height() // 2) - (gerekli_yukseklik // 2)) 
        
        yillik_win.geometry(f"{gerekli_genislik}x{gerekli_yukseklik}+{son_x}+{son_y}")
