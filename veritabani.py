import sqlite3

class VeritabaniYoneticisi:
    def __init__(self, db_yolu):
        self.db_yolu = db_yolu
        self.conn = None
        self.cursor = None
        self.baglan_ve_hazirla()

    def baglan_ve_hazirla(self):
        # Veritabanına bağlanır
        self.conn = sqlite3.connect(self.db_yolu, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # 1. TABLOLARI OLUŞTURMA (Eksik olan kısmı geri getirdik)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ogrenciler (no TEXT, ad_soyad TEXT, sube TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS devamsizliklar (id TEXT, no TEXT, tarih TEXT, tur TEXT, gun TEXT, secili INTEGER)")

        # 2. ADIM: İNDEKSLER (Fihrist Motoru - "self" takısı eklendi ve tablo adları devamsizliklar olarak düzeltildi)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_no ON ogrenciler (no)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_devamsizlik_no ON devamsizliklar (no)")
        self.conn.commit()

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
        if self.conn:
            self.conn.close()
