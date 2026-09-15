import sqlite3
import threading

class VeritabaniYoneticisi:
    def __init__(self, db_yolu):
        self.db_yolu = db_yolu
        self._local = threading.local()
        # Veritabanı dosyası ve tabloları ilk açılışta bir kez oluşturulur.
        self._init_db()

    def _init_db(self):
        bellek_veritabani = self.db_yolu == ":memory:"
        conn = self.conn if bellek_veritabani else sqlite3.connect(self.db_yolu)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS ogrenciler (no TEXT, ad_soyad TEXT, sube TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS devamsizliklar (id TEXT, no TEXT, tarih TEXT, tur TEXT, gun TEXT, secili INTEGER)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_no ON ogrenciler (no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devamsizlik_no ON devamsizliklar (no)")
        cursor.execute("CREATE TABLE IF NOT EXISTS personel (ad_soyad TEXT, brans TEXT, gorev TEXT, grup TEXT)")
        
        try:
            cursor.execute("ALTER TABLE personel ADD COLUMN grup TEXT")
        except sqlite3.OperationalError:
            pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personel_ad ON personel (ad_soyad)")
        conn.commit()
        if not bellek_veritabani:
            conn.close()

    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_yolu, check_same_thread=False)
        return self._local.conn

    @property
    def cursor(self):
        if not hasattr(self._local, "cursor"):
            self._local.cursor = self.conn.cursor()
        return self._local.cursor

    def baglan_ve_hazirla(self):
        # Geriye dönük uyumluluk (api.py çağırıyor olabilir)
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
            print(f"Veritabanı okuma hatası: {e}")
            return [], []

    def kaydet(self, ogrenciler, devamsizliklar):
        # 3. ADIM: TOPLU İŞLEM MODU (Transaction Motoru Kuruldu!)
        try:
            # Veritabanına diski yormamasını, tüm işlemleri tek seferde beklemesini söylüyoruz
            self.cursor.execute("BEGIN TRANSACTION")
            
            self.cursor.execute("DELETE FROM ogrenciler")
            self.cursor.executemany("INSERT INTO ogrenciler VALUES (?, ?, ?)", [(o['no'], o['ad_soyad'], o['sube']) for o in ogrenciler])
            
            self.cursor.execute("DELETE FROM devamsizliklar")
            kalici_kayitlar = [(d['id'], d['no'], d['tarih'], d['tur'], d['gun'], 1 if d.get('secili') else 0) for d in devamsizliklar]
            self.cursor.executemany("INSERT INTO devamsizliklar VALUES (?, ?, ?, ?, ?, ?)", kalici_kayitlar)
            
            # Tüm o devasa ekleme işlemleri bittiğinde tek bir komutla diske şimşek gibi yazdırıyoruz
            self.conn.commit()
            return True, ""
        except Exception as e:
            # Eğer yükleme sırasında bir hata olursa sistemi çökertme, verileri eski haline (geri) al
            self.conn.rollback()
            return False, str(e)

    def sifirla(self):
        # Tüm tabloları temizler
        self.cursor.execute("DELETE FROM ogrenciler")
        self.cursor.execute("DELETE FROM devamsizliklar")
        self.conn.commit()

    def kapat(self):
        # Kapanışta bağlantıyı güvenle keser
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn
            if hasattr(self._local, "cursor"):
                del self._local.cursor
