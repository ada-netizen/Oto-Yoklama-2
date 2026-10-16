import sqlite3
import threading
import logging

class VeritabaniYoneticisi:
    def __init__(self, db_yolu):
        self.db_yolu = db_yolu
        self._local = threading.local()
        self._son_snapshot = None
        # Veritabanı dosyası ve tabloları ilk açılışta bir kez oluşturulur.
        self._init_db()

    def _init_db(self):
        bellek_veritabani = self.db_yolu == ":memory:"
        conn = self.conn if bellek_veritabani else sqlite3.connect(self.db_yolu, timeout=30.0)
        cursor = conn.cursor()
        if not bellek_veritabani:
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
            except Exception as pe:
                logging.warning(f"WAL modu ayarlanamadı: {pe}")

        cursor.execute("CREATE TABLE IF NOT EXISTS ogrenciler (no TEXT, ad_soyad TEXT, sube TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS devamsizliklar (id TEXT, no TEXT, tarih TEXT, tur TEXT, gun TEXT, secili INTEGER)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_no ON ogrenciler (no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_sube ON ogrenciler (sube)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devamsizlik_no ON devamsizliklar (no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devamsizlik_tarih ON devamsizliklar (tarih)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devamsizlik_tur ON devamsizliklar (tur)")
        cursor.execute("CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tc_no TEXT, unvan TEXT, brans TEXT, gorev TEXT, grup TEXT, il_ilce TEXT, kurum_adi TEXT, kurum_kodu TEXT, kurumda_baslama TEXT, kariyer TEXT, kademe_derece TEXT, ogrenim_durumu TEXT, cinsiyet TEXT, kan_grubu TEXT, dogum_tarihi TEXT, goreve_baslama TEXT, kurum_sicil_no TEXT, emekli_sicil_no TEXT, arsiv_no TEXT, telefon TEXT, eposta TEXT, notlar TEXT, aktif INTEGER DEFAULT 1)")
        cursor.execute("CREATE TABLE IF NOT EXISTS saglik_raporlari (id INTEGER PRIMARY KEY AUTOINCREMENT, personel_ad TEXT, baslangic_tarihi TEXT, bitis_tarihi TEXT, gun_sayisi INTEGER, aciklama TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS personel_rapor_kesinti (personel_ad TEXT PRIMARY KEY, onceden_kesilen_gun INTEGER)")
        
        personel_kolonlar = [
            ("tc_no", "TEXT"),
            ("unvan", "TEXT"),
            ("il_ilce", "TEXT"),
            ("kurum_adi", "TEXT"),
            ("kurum_kodu", "TEXT"),
            ("kurumda_baslama", "TEXT"),
            ("kariyer", "TEXT"),
            ("kademe_derece", "TEXT"),
            ("ogrenim_durumu", "TEXT"),
            ("cinsiyet", "TEXT"),
            ("kan_grubu", "TEXT"),
            ("dogum_tarihi", "TEXT"),
            ("goreve_baslama", "TEXT"),
            ("kurum_sicil_no", "TEXT"),
            ("emekli_sicil_no", "TEXT"),
            ("arsiv_no", "TEXT"),
            ("telefon", "TEXT"),
            ("eposta", "TEXT"),
            ("notlar", "TEXT"),
            ("aktif", "INTEGER DEFAULT 1")
        ]
        for col_name, col_type in personel_kolonlar:
            try:
                cursor.execute(f"ALTER TABLE personel ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personel_ad ON personel (ad_soyad)")
        cursor.execute("CREATE TABLE IF NOT EXISTS uretilen_evraklar (id INTEGER PRIMARY KEY AUTOINCREMENT, tur TEXT, personel_ad TEXT, brans TEXT, tarih TEXT)")
        
        try:
            cursor.execute("PRAGMA user_version;")
            ver = cursor.fetchone()[0]
            if ver < 1:
                cursor.execute("PRAGMA user_version = 1;")
        except Exception as e:
            logging.warning(f"user_version ayarlanamadı: {e}")
            
        conn.commit()
        if not bellek_veritabani:
            conn.close()

    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            c = sqlite3.connect(self.db_yolu, timeout=30.0, check_same_thread=False)
            try:
                c.execute("PRAGMA busy_timeout=30000;")
                if self.db_yolu != ":memory:":
                    c.execute("PRAGMA journal_mode=WAL;")
                    c.execute("PRAGMA synchronous=NORMAL;")
            except Exception as pe:
                logging.warning(f"Bağlantı pragma ayarlanamadı: {pe}")
            self._local.conn = c
        return self._local.conn

    @property
    def cursor(self):
        if not hasattr(self._local, "cursor"):
            self._local.cursor = self.conn.cursor()
        return self._local.cursor

    def baglan_ve_hazirla(self):
        # Geriye dönük uyumluluk
        pass

    def yukle(self):
        # RAM'e çekilecek verileri listeler halinde hızlıca döndürür
        try:
            self.cursor.execute("SELECT no, ad_soyad, sube FROM ogrenciler")
            ogrenciler = [{'no': r[0], 'ad_soyad': r[1], 'sube': r[2]} for r in self.cursor.fetchall()]
            
            self.cursor.execute("SELECT id, no, tarih, tur, gun, secili FROM devamsizliklar")
            devamsizliklar = [{'id': r[0], 'no': r[1], 'tarih': r[2], 'tur': r[3], 'gun': r[4], 'secili': False} for r in self.cursor.fetchall()]
            return ogrenciler, devamsizliklar
        except Exception as e:
            logging.error(f"Veritabanı okuma hatası: {e}")
            return [], []

    def kaydet(self, ogrenciler, devamsizliklar, snapshot_al=True):
        # Toplu işlem modu (Transaction Motoru)
        try:
            if snapshot_al:
                mevcut_ogr, mevcut_dev = self.yukle()
                if mevcut_ogr or mevcut_dev:
                    self._son_snapshot = (mevcut_ogr, mevcut_dev)
                    
            self.cursor.execute("BEGIN TRANSACTION")
            
            self.cursor.execute("DELETE FROM ogrenciler")
            self.cursor.executemany("INSERT INTO ogrenciler VALUES (?, ?, ?)", [(o['no'], o['ad_soyad'], o['sube']) for o in ogrenciler])
            
            self.cursor.execute("DELETE FROM devamsizliklar")
            kalici_kayitlar = [(d['id'], d['no'], d['tarih'], d['tur'], d['gun'], 1 if d.get('secili') else 0) for d in devamsizliklar]
            self.cursor.executemany("INSERT INTO devamsizliklar VALUES (?, ?, ?, ?, ?, ?)", kalici_kayitlar)
            
            self.conn.commit()
            return True, ""
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Veritabanı kaydetme hatası: {e}")
            return False, str(e)

    def son_islemi_geri_al(self):
        """Son yapılan kaydet işlemini geri alarak bir önceki veritabanı durumuna döner."""
        if not self._son_snapshot:
            return False, "Geri alınabilecek önceki bir işlem bulunamadı."
        onceki_ogrenciler, onceki_devamsizliklar = self._son_snapshot
        self._son_snapshot = None
        return self.kaydet(onceki_ogrenciler, onceki_devamsizliklar, snapshot_al=False)

    def yedekle(self, hedef_yol=None):
        """SQLite Online Backup API kullanarak veritabanını kilitlenmeden canlı yedekler."""
        if self.db_yolu == ":memory:":
            return False, "Bellek veritabanı yedeklenemez."
        try:
            import os, datetime
            if not hedef_yol:
                yedek_dizin = os.path.join(os.path.dirname(self.db_yolu) or ".", "yedekler")
                os.makedirs(yedek_dizin, exist_ok=True)
                zaman_damgasi = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                hedef_yol = os.path.join(yedek_dizin, f"okul_veritabani_oto_yedek_{zaman_damgasi}.db")
            
            yedek_conn = sqlite3.connect(hedef_yol)
            with yedek_conn:
                self.conn.backup(yedek_conn)
            yedek_conn.close()
            return True, hedef_yol
        except Exception as e:
            logging.error(f"Canlı SQLite yedekleme hatası: {e}")
            return False, str(e)

    def sifirla(self):
        # Tüm tabloları temizler
        self.cursor.execute("DELETE FROM ogrenciler")
        self.cursor.execute("DELETE FROM devamsizliklar")
        self.cursor.execute("DELETE FROM uretilen_evraklar")
        self.conn.commit()

    def kapat(self):
        # Kapanışta bağlantıyı güvenle keser
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn
            if hasattr(self._local, "cursor"):
                del self._local.cursor
