import os, logging, tempfile, re, shutil, uuid
import platform, subprocess
from datetime import datetime, timedelta
import pandas as pd
from dependencies import yollar, db
from sistem_motoru import SistemMotoru
from models import *

MAX_IMPORT_SIZE = 25 * 1024 * 1024
ALLOWED_IMPORT_EXTENSIONS = {".xlsx", ".xls", ".csv"}

def dosyayi_otomatik_ac(dosya_yolu):
    """Oluşturulan PDF veya Excel dosyasını bilgisayarın varsayılan programıyla anında açar"""
    try:
        import platform, subprocess
        if platform.system() == 'Windows':
            norm_yol = os.path.normpath(dosya_yolu)
            os.startfile(norm_yol)
        elif platform.system() == 'Darwin':
            subprocess.call(('open', dosya_yolu))
        else:
            subprocess.call(('xdg-open', dosya_yolu))
    except Exception as e:
        logging.error(f"dosyayi_otomatik_ac hatasi ({dosya_yolu}): {e}")

def _sablon_excel_yolu_olustur():
    adaylar = [
        os.path.join(os.getcwd(), "sablonlar", "sablon.xlsx"),
        os.path.join(os.path.dirname(__file__), "sablonlar", "sablon.xlsx"),
    ]
    for yol in adaylar:
        if not os.path.exists(yol):
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Sablon"
                ws.append(["Cins / Ad", "Miktar", "Birim"])
                for sutun in ["A", "B", "C"]:
                    ws[f"{sutun}1"].font = openpyxl.styles.Font(bold=True)
                ws.freeze_panes = "A2"
                wb.save(yol)
            except Exception:
                continue
        if os.path.exists(yol):
            return yol
    return os.path.join(os.getcwd(), "sablonlar", "sablon.xlsx")


def excel_yukleme_dogrula(dosya):
    """Excel/CSV yüklemelerini boyut ve uzantı açısından kontrol eder."""
    dosya_adi = dosya.filename or ""
    uzanti = os.path.splitext(dosya_adi)[1].lower()
    if uzanti not in ALLOWED_IMPORT_EXTENSIONS:
        return None, "Yalnızca XLSX, XLS veya CSV dosyaları yüklenebilir."

    try:
        dosya.file.seek(0, os.SEEK_END)
        boyut = dosya.file.tell()
        dosya.file.seek(0)
    except (AttributeError, OSError) as e:
        return None, f"Dosya okunamadı: {e}"

    if boyut == 0:
        return None, "Yüklenen dosya boş."
    if boyut > MAX_IMPORT_SIZE:
        return None, "Dosya boyutu 25 MB sınırını aşamaz."
    return uzanti, None


def islem_logla(seviye, islem, mesaj):
    """Kullanıcıya gösterilebilecek hassas olmayan işlem kaydı oluşturur."""
    if seviye.lower() == "hata":
        logging.error(f"İşlem Hatası: {islem} - {mesaj}")
    else:
        logging.info(f"İşlem Kaydı: {islem} - {mesaj}")
        
    kayit = {
        "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seviye": seviye,
        "islem": islem,
        "mesaj": mesaj,
    }
    islem_loglari.append(kayit)
    del islem_loglari[:-200]
    try:
        with open(yollar["LOG"], "a", encoding="utf-8") as dosya:
            dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except OSError:
        pass

from contextlib import contextmanager
from fastapi import UploadFile

@contextmanager
def gecici_dosya_olustur(dosya: UploadFile, prefix="temp_"):
    # Güvenli geçici dosya adı: Türkçe karakter veya özel karakter içeren
    # orijinal dosya adı yerine uuid tabanlı güvenli bir ad kullanıyoruz.
    uzanti = os.path.splitext(dosya.filename or ".pdf")[1] or ".pdf"
    temp_yol = f"{prefix}{uuid.uuid4().hex[:8]}{uzanti}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        yield temp_yol
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass


_son_ayarlar_mtime = 0
ayarlar_cache = None

def ayarlari_al():
    """Ayarları sadece dosya degistiginde okur (Cache)."""
    global ayarlar_cache, _son_ayarlar_mtime
    from sistem_motoru import SistemMotoru
    import os
    from dependencies import yollar
    try:
        mtime = os.path.getmtime(yollar["AYARLAR"])
    except OSError:
        mtime = 0
        
    if mtime != _son_ayarlar_mtime or _son_ayarlar_mtime == 0 or ayarlar_cache is None:
        ayarlar_cache = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
        _son_ayarlar_mtime = mtime
    return ayarlar_cache


def pdf_klasoru_hazirla():
    ayar = ayarlari_al()
    ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor):
        os.makedirs(ana_klasor)
    return ana_klasor, ayar


def _personel_grup_tahmin_et(gorev):
    g = str(gorev).upper()
    if "ÖĞRETMEN" in g:
        return "Öğretmenler"
    if g in ["OKUL MÜDÜRÜ", "MÜDÜR YARDIMCISI", "MÜDÜR BAŞYARDIMCISI", "VHKİ", "MEMUR"]:
        return "İdare"
    return "Diğer Personel"


def _excel_sutunu_bul(sutunlar, adaylar):
    """Excel başlıklarındaki boşluk ve Türkçe büyük/küçük harf farklarını tolere eder."""
    normalize = lambda deger: re.sub(r"[^A-ZÇĞİÖŞÜ0-9]", "", str(deger).strip().upper())
    aday_seti = {normalize(aday) for aday in adaylar}
    for sutun in sutunlar:
        if normalize(sutun) in aday_seti:
            return sutun
    return None


def _rapor_verisi_hazirla(tur, ozel_deger):
    ogrenci_listesi, devamsizlik_listesi = db.yukle()
    gruplu = {}
    for dev in devamsizlik_listesi:
        no = str(dev['no']).strip()
        gruplu.setdefault(no, []).append(dev)

    hedef_tarih_obj = None
    if tur == "tarih_bazli":
        try:
            gg, aa, yy = map(int, str(ozel_deger).split('/'))
            hedef_tarih_obj = datetime(yy, aa, gg)
        except Exception as e:
            logging.error(f"_rapor_verisi_hazirla tarih formati hatasi: {e}")
            return None, "Tarih formatı hatalı! (GG/AA/YYYY olmalı)"

    veri = []
    for ogr in ogrenci_listesi:
        ogr_no = str(ogr['no']).strip()
        ogr_devleri = gruplu.get(ogr_no, [])
        ozsz, ozrl = VeriAraclari.hesapla_devamsizlik(ogr_no, ogr_devleri, [])
        gosterilen_sube = VeriAraclari.kisa_sube_adi(ogr['sube'])

        if tur == "ozursuz" and ozsz < 10: continue
        if tur == "ozurlu" and ozrl < 20: continue
        if tur == "gun_siniri" and ozsz < float(ozel_deger): continue
        if tur == "sube_bazli" and gosterilen_sube.replace(" ", "") != str(ozel_deger).replace(" ", ""): continue

        if tur == "tarih_bazli":
            bulundu = False
            dev_turu = ""
            for dev in ogr_devleri:
                if dev['tur'].upper() not in ["D", "ÖY", "SY"]:
                    continue
                try:
                    gun_mik = float(VeriAraclari.temiz_sure(dev['gun']))
                    tam_g = int(gun_mik) if gun_mik >= 1 else 1
                    bd, bm, by = map(int, VeriAraclari.tarih_formatla(dev['tarih']).split('/'))
                    bas_tarih = datetime(by, bm, bd)
                    for i in range(tam_g):
                        g_t = bas_tarih + timedelta(days=i)
                        if g_t.weekday() < 5 and g_t.date() == hedef_tarih_obj.date():
                            bulundu = True
                            dev_turu = dev['tur'].upper()
                            break
                    if bulundu:
                        break
                except Exception as e:
                    logging.error(f"_rapor_verisi_hazirla dongu hatasi: {e}")
                    pass
            if not bulundu:
                continue
            veri.append([gosterilen_sube, ogr_no, ogr['ad_soyad'], dev_turu])
        else:
            veri.append([gosterilen_sube, ogr_no, ogr['ad_soyad'], ozsz])

    if tur == "tarih_bazli":
        def anahtar(x):
            r = re.findall(r'\d+', str(x[0]))
            return (int(r[0]) if r else 99, x[0], x[1])
        veri.sort(key=anahtar)
    else:
        veri.sort(key=lambda x: x[3], reverse=True)
    return veri, None


