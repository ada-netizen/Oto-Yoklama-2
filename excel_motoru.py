import pandas as pd
import uuid
from araclar import VeriAraclari

class ExcelMotoru:
    @staticmethod
    def tabloyu_guvenli_oku(dosya_yolu, header=None, dtype=str):
        """
        MEB e-Okul ve diğer kaynaklardan gelen her türlü Excel (.xlsx, .xls), 
        sahte XLS (HTML/XML) ve CSV formatını doğru motor ve encoding ile okur.
        """
        try:
            with open(dosya_yolu, 'rb') as f:
                magic = f.read(8)
        except Exception as e:
            raise ValueError(f"Dosya okunamadı: {e}")

        # 1. Gerçek .xls (OLE2 Binary Compound: \xd0\xcf\x11\xe0...)
        if magic.startswith(b'\xd0\xcf\x11\xe0'):
            try:
                return pd.read_excel(dosya_yolu, engine='xlrd', header=header, dtype=dtype)
            except Exception:
                pass

        # 2. Gerçek .xlsx (ZIP PK\x03\x04...)
        if magic.startswith(b'PK\x03\x04'):
            try:
                return pd.read_excel(dosya_yolu, engine='openpyxl', header=header, dtype=dtype)
            except Exception:
                pass

        # 3. Otomatik read_excel denemesi
        try:
            return pd.read_excel(dosya_yolu, header=header, dtype=dtype)
        except Exception:
            pass

        # 4. Motorları zorlayarak deneme
        try:
            return pd.read_excel(dosya_yolu, engine='xlrd', header=header, dtype=dtype)
        except Exception:
            pass
        try:
            return pd.read_excel(dosya_yolu, engine='openpyxl', header=header, dtype=dtype)
        except Exception:
            pass

        # 5. Sahte XLS (HTML Tablo - e-Okul / MEBBİS formatı)
        for enc in ['cp1254', 'utf-8', 'utf-8-sig', 'iso-8859-9']:
            try:
                df_list = pd.read_html(dosya_yolu, header=header, encoding=enc)
                if df_list:
                    df = max(df_list, key=len)
                    if dtype is not None:
                        df = df.astype(dtype)
                    return df
            except Exception:
                continue

        # 6. CSV Formatı
        for enc in ['utf-8-sig', 'cp1254', 'utf-8', 'iso-8859-9']:
            try:
                return pd.read_csv(dosya_yolu, header=header, dtype=dtype, encoding=enc, on_bad_lines='skip')
            except Exception:
                continue

        raise ValueError("Dosya Excel, HTML veya CSV olarak çözümlenemedi.")

    @staticmethod
    def ogrenci_oku(dosya_yolu, mevcut_ogrenciler):
        yeni_liste = []
        try:
            import re
            df = ExcelMotoru.tabloyu_guvenli_oku(dosya_yolu, header=None, dtype=str)
            if df.empty:
                return None, "Excel dosyası boş veya okunamadı."

            mevcut_nolar = {str(o['no']).strip() for o in mevcut_ogrenciler}
            yeni_nolar = set()

            # --- 1. E-OKUL ÇOKLU SINIF LİSTESİ ŞABLONU TESPİTİ ---
            is_eokul = False
            for idx in range(min(50, len(df))):
                row_str = " ".join([str(x) for x in df.iloc[idx].values if pd.notna(x)]).lower()
                if "sınıf listesi" in row_str or "sinif listesi" in row_str:
                    is_eokul = True
                    break

            if is_eokul:
                aktif_sube = ""
                col_no_idx = 1
                col_ad_idx = 3
                col_soyad_idx = 7

                for index, row in df.iterrows():
                    row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                    # Yeni bir sınıf başlığı satırı mı?
                    if "sınıf listesi" in row_str.lower() or "sinif listesi" in row_str.lower():
                        for val in row.values:
                            v_str = str(val) if pd.notna(val) else ""
                            if "sınıf listesi" in v_str.lower() or "sinif listesi" in v_str.lower():
                                raw = re.split(r's[ıi]n[ıi]f\s+listesi', v_str, flags=re.IGNORECASE)[0]
                                if "Müdürlüğü" in raw: raw = raw.split("Müdürlüğü")[-1]
                                if "Mdrl" in raw: raw = raw.split("Mdrl")[-1]
                                raw = raw.replace("\n", " ").strip()
                                if "AL -" in raw: raw = raw.split("AL -")[-1].strip()
                                if "AMP -" in raw: raw = raw.split("AMP -")[-1].strip()
                                aktif_sube = VeriAraclari.kisa_sube_adi(raw)
                                break
                        continue

                    # Tablo sütun başlıkları satırı mı? (Örn: S.No, Öğrenci No, Adı, Soyadı)
                    row_cells_clean = [
                        str(x).strip().upper().replace('.', '').replace('İ', 'I').replace('Ğ', 'G').replace('Ş', 'S').replace('Ö', 'O').replace('Ü', 'U')
                        for x in row.values if pd.notna(x)
                    ]
                    if any("OGRENCI NO" in c for c in row_cells_clean):
                        for c_idx, cell_val in enumerate(row.values):
                            c_clean = str(cell_val).strip().upper().replace('.', '').replace('İ', 'I').replace('Ğ', 'G').replace('Ş', 'S').replace('Ö', 'O').replace('Ü', 'U')
                            if "OGRENCI NO" in c_clean or c_clean == "NO":
                                col_no_idx = c_idx
                            elif c_clean in ["ADI", "AD", "OGRENCI ADI"]:
                                col_ad_idx = c_idx
                            elif c_clean in ["SOYADI", "SOYAD", "OGRENCI SOYADI"]:
                                col_soyad_idx = c_idx
                        continue

                    # Öğrenci veri satırı mı?
                    max_col = max(col_no_idx, col_ad_idx, col_soyad_idx)
                    if len(row) > max_col and pd.notna(row.iloc[col_no_idx]):
                        val_no = str(row.iloc[col_no_idx]).replace('.0', '').strip()
                        if val_no.isdigit() and "öğrenci" not in str(row.iloc[col_no_idx]).lower():
                            ad = str(row.iloc[col_ad_idx]).strip() if pd.notna(row.iloc[col_ad_idx]) else ""
                            soyad = str(row.iloc[col_soyad_idx]).strip() if pd.notna(row.iloc[col_soyad_idx]) else ""
                            ad_soyad = f"{ad} {soyad}".strip()
                            if ad_soyad and val_no not in mevcut_nolar and val_no not in yeni_nolar:
                                yeni_liste.append({'no': val_no, 'ad_soyad': ad_soyad, 'sube': aktif_sube})
                                yeni_nolar.add(val_no)

                if yeni_liste:
                    return yeni_liste, None

            # --- 2. GENEL DÜZ TABLO ŞABLONU (Fuzzy Header Detection) ---
            no_col = None
            ad_col = None
            soyad_col = None
            ad_soyad_col = None
            sube_col = None
            header_row_idx = -1

            for idx in range(min(20, len(df))):
                cur_no_col = None
                cur_ad_col = None
                cur_soyad_col = None
                cur_ad_soyad_col = None
                cur_sube_col = None

                for col_idx, cell in enumerate(df.iloc[idx].values):
                    c_clean = str(cell).strip().upper().replace('.', '').replace('İ', 'I').replace('Ğ', 'G').replace('Ş', 'S').replace('Ö', 'O').replace('Ü', 'U')
                    if c_clean in ['NO', 'OGRENCI NO', 'OKUL NO', 'NUMARA', 'OGR NO'] and cur_no_col is None:
                        cur_no_col = col_idx
                    elif c_clean in ['AD SOYAD', 'ADI SOYADI', 'OGRENCI ADI SOYADI', 'AD VE SOYAD'] and cur_ad_soyad_col is None:
                        cur_ad_soyad_col = col_idx
                    elif c_clean in ['AD', 'ADI', 'OGRENCI ADI'] and cur_ad_col is None:
                        cur_ad_col = col_idx
                    elif c_clean in ['SOYAD', 'SOYADI', 'OGRENCI SOYADI'] and cur_soyad_col is None:
                        cur_soyad_col = col_idx
                    elif c_clean in ['SUBE', 'SUBESI', 'SINIF', 'SINIFI', 'SINIF/SUBE', 'SINIF / SUBE', 'SINIF SUBE'] and cur_sube_col is None:
                        cur_sube_col = col_idx

                if cur_no_col is not None and (cur_ad_soyad_col is not None or (cur_ad_col is not None and cur_soyad_col is not None)):
                    header_row_idx = idx
                    no_col = cur_no_col
                    ad_col = cur_ad_col
                    soyad_col = cur_soyad_col
                    ad_soyad_col = cur_ad_soyad_col
                    sube_col = cur_sube_col
                    break

            if header_row_idx != -1 and no_col is not None:
                for idx in range(header_row_idx + 1, len(df)):
                    row = df.iloc[idx]
                    val_no = str(row.iloc[no_col]).replace('.0', '').strip() if pd.notna(row.iloc[no_col]) else ""
                    if not val_no or not val_no.isdigit():
                        continue

                    if ad_soyad_col is not None:
                        ad_soyad = str(row.iloc[ad_soyad_col]).strip() if pd.notna(row.iloc[ad_soyad_col]) else ""
                    else:
                        ad = str(row.iloc[ad_col]).strip() if ad_col is not None and pd.notna(row.iloc[ad_col]) else ""
                        soyad = str(row.iloc[soyad_col]).strip() if soyad_col is not None and pd.notna(row.iloc[soyad_col]) else ""
                        ad_soyad = f"{ad} {soyad}".strip()

                    sube = VeriAraclari.kisa_sube_adi(str(row.iloc[sube_col])) if sube_col is not None and pd.notna(row.iloc[sube_col]) else ""

                    if ad_soyad and val_no not in mevcut_nolar and val_no not in yeni_nolar:
                        yeni_liste.append({'no': val_no, 'ad_soyad': ad_soyad, 'sube': sube})
                        yeni_nolar.add(val_no)

                if yeni_liste:
                    return yeni_liste, None

            return yeni_liste, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def devamsizlik_oku(dosya_yolu, mevcut_devamsizliklar):
        yeni_liste = []
        eklenen = 0
        try:
            df = ExcelMotoru.tabloyu_guvenli_oku(dosya_yolu, header=None, dtype=str)
            if df.empty: return None, 0, "Excel dosyası boş veya okunamadı."

            mevcut_hash = {f"{str(d['no']).strip()}_{d['tarih']}_{d['tur'].upper()}" for d in mevcut_devamsizliklar}
            yeni_hash = set()
            
            gecerli_turler = ["D", "ÖY", "SY", "İ", "I", "S", "SV", "G", "F", "N", "R"]
            son_okunan_no = ""
            
            for index, row in df.iterrows():
                vals = [str(x).strip() for x in row.values if pd.notna(x) and str(x).strip() != "" and str(x).strip().lower() != "nan"]
                if len(vals) < 4: continue
                
                ogr_no = vals[0].replace('.0', '').strip()
                if ogr_no.isdigit():
                    pass 
                elif len(vals) >= 5 and vals[1].replace('.0', '').isdigit(): 
                    ogr_no = vals[1].replace('.0', '').strip()
                else: 
                    ogr_no = "" 

                if ogr_no: 
                    son_okunan_no = ogr_no 
                else: 
                    ogr_no = son_okunan_no 
                
                if not ogr_no: continue
                    
                tarih_ham = vals[-3]
                tur = vals[-2].upper()
                gun_ham = vals[-1]
                
                if tur in gecerli_turler:
                    tarih_str = VeriAraclari.excel_tarih_cevir(tarih_ham)
                    
                    # MUCİZE SÜRE ZIRHI: Yarım, 0.5, Tam gibi her formatı ezer ve doğru rakama çevirir!
                    s_temiz = str(gun_ham).upper().replace(',', '.').replace('YARIM', '0.5').replace('TAM', '1').strip()
                    if s_temiz.endswith('.0'): s_temiz = s_temiz[:-2]
                    s_rakam = "".join([c for c in s_temiz if c.isdigit() or c == '.'])
                    if not s_rakam or s_rakam == ".": s_rakam = "1"
                    
                    kayit_kimligi = f"{ogr_no}_{tarih_str}_{tur}"
                    if kayit_kimligi not in mevcut_hash and kayit_kimligi not in yeni_hash:
                        yeni_liste.append({
                            'id': str(uuid.uuid4().hex), 
                            'no': ogr_no, 
                            'tarih': tarih_str, 
                            'tur': tur, 
                            'gun': s_rakam, # <--- Düzeltilmiş süre burada kaydediliyor
                            'secili': False
                        })
                        yeni_hash.add(kayit_kimligi)
                        eklenen += 1

            return yeni_liste, eklenen, None
        except Exception as e:
            return None, 0, f"Excel Okuma Hatası: {str(e)}"

    def esik_raporu_excel_ciz(self, veri, kayit_yeri):
        df = pd.DataFrame(veri, columns=['Sınıf/Şube', '5-14 Gün', '15-24 Gün', '25-39 Gün', '40+ Gün'])
        df.to_excel(kayit_yeri, index=False)


    @staticmethod
    def ihale_oku(dosya_yolu):
        try:
            xl = pd.ExcelFile(dosya_yolu)
            sheet_name = xl.sheet_names[1] if len(xl.sheet_names) > 1 else xl.sheet_names[0]
            
            df = xl.parse(sheet_name)
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            
            def safe_float(val, default=0.0):
                if pd.isna(val): return default
                try:
                    s = str(val).replace('₺', '').replace('$', '').strip()
                    if ',' in s and '.' not in s: s = s.replace(',', '.')
                    elif ',' in s and '.' in s: s = s.replace(',', '')
                    return float(s)
                except: return default

            kalemler = []
            sira = 1
            for idx, row in df.iterrows():
                try:
                    cins = str(row.iloc[1]).strip()
                    if cins and cins.lower() not in ['nan', 'c i n s i', 'none', 'satın alinacak malin']:
                        miktar_raw = row.iloc[2]
                        birim = row.iloc[3]
                        
                        if pd.notna(cins) and pd.notna(miktar_raw):
                            kalemler.append({
                                "sira": sira,
                                "cins": cins,
                                "miktar": safe_float(miktar_raw, 1.0),
                                "birim": str(birim).strip() if pd.notna(birim) else "Adet",
                                "f1": safe_float(row.iloc[4], 0.0),
                                "f2": safe_float(row.iloc[5], 0.0),
                                "f3": safe_float(row.iloc[6], 0.0),
                            })
                            sira += 1
                except:
                    pass
            return kalemler, ""
        except Exception as e:
            return None, str(e)

    @staticmethod
    def akilli_kademe_derece(val):
        """
        Excel'in '1/4' derece/kademe bilgisini tarih (örn: 1 Nisan, 2026-04-01) 
        olarak algılaması durumunda otomatik olarak gün ve ayı ayırıp 1/4'e geri dönüştürür.
        """
        if val is None or pd.isna(val) or val == '':
            return '-'
        from datetime import datetime, date
        if isinstance(val, (datetime, date, pd.Timestamp)):
            return f"{val.day}/{val.month}"
        s = str(val).strip()
        if s.lower() in ['nan', 'none', '<na>', 'nat', '-', '']:
            return '-'
        if ' 00:00:00' in s:
            s = s.replace(' 00:00:00', '').strip()
            
        import re
        # 1. ISO format: 2026-04-01 -> 1/4 (Yıl-Ay-Gün -> Gün/Ay)
        m_iso = re.match(r'^\d{4}-(\d{1,2})-(\d{1,2})$', s)
        if m_iso:
            return f"{int(m_iso.group(2))}/{int(m_iso.group(1))}"
            
        # 2. Türkçe metin ayı formatı: 1-Nis, 1 Nisan, 1 Nis 2026
        ay_map = {
            'oca': 1, 'ocak': 1, 'sub': 2, 'şub': 2, 'şubat': 2, 'mar': 3, 'mart': 3,
            'nis': 4, 'nisan': 4, 'may': 5, 'mayıs': 5, 'haz': 6, 'haziran': 6,
            'tem': 7, 'temmuz': 7, 'agu': 8, 'ağu': 8, 'ağustos': 8, 'eyl': 9, 'eylül': 9,
            'eki': 10, 'ekim': 10, 'kas': 11, 'kasım': 11, 'ara': 12, 'aralık': 12
        }
        m_word = re.match(r'^(\d{1,2})[\s\-./]+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)', s)
        if m_word:
            day = int(m_word.group(1))
            month_word = m_word.group(2).lower()[:3]
            if month_word in ay_map:
                return f"{day}/{ay_map[month_word]}"
                
        # 3. TR tarih formatı: 01.04.2026 veya 01/04/2026
        m_tr_date = re.match(r'^0?(\d{1,2})[./\-]0?(\d{1,2})[./\-]\d{2,4}$', s)
        if m_tr_date:
            return f"{int(m_tr_date.group(1))}/{int(m_tr_date.group(2))}"
            
        # 4. Standart oran: 1/4, 1-4, 3/2
        m_simple = re.match(r'^(\d{1,2})\s*[/\\-]\s*(\d{1,2})$', s)
        if m_simple:
            return f"{int(m_simple.group(1))}/{int(m_simple.group(2))}"
            
        return s

    @staticmethod
    def pano_metnini_tabloya_cevir(kaynak):
        """
        Kullanıcının panodan kopyalayıp yapıştırdığı (HTML veya TSV/metin) tablo verisini
        satır/sütun sayısı uyumsuzluklarından (ragged rows, uneven tabs, ParserError) 
        etkilenmeden güvenli, hizalanmış bir pandas DataFrame'e dönüştürür.
        """
        import io
        import os
        import re

        if isinstance(kaynak, pd.DataFrame):
            return kaynak
        if not isinstance(kaynak, str):
            return pd.DataFrame()

        s = kaynak.strip()
        if not s:
            return pd.DataFrame()

        # 1. HTML tablo denemesi
        if '<table' in s.lower():
            try:
                df_list = pd.read_html(io.StringIO(s), header=None)
                if df_list and not df_list[0].empty:
                    return df_list[0]
            except Exception:
                pass

        # 2. Satır bazlı TSV / metin çözümleme
        lines = [l for l in s.splitlines() if l.strip()]
        if not lines:
            return pd.DataFrame()

        sep = '\t' if '\t' in s else (';' if ';' in s else '\t')
        raw_rows = [[c.strip() for c in l.split(sep)] for l in lines]
        if not raw_rows:
            return pd.DataFrame()

        # Akıllı Kolon Hizalama (TC Sütununa Göre Ofset Tespiti)
        # MEBBİS tablolarında bazen başlık satırında seçim/ikon sütunu kopyalanmazken
        # veri satırlarında ilk sütun boş ('') olarak kopyalanır (23 başlığa karşılık 24 veri hücresi).
        h0 = raw_rows[0]
        tc_h_idx = next((i for i, c in enumerate(h0) if 'tc' in c.lower()), -1)
        if tc_h_idx != -1 and len(raw_rows) > 1:
            d_rows = raw_rows[1:]
            tc_d_indices = [i for r in d_rows for i, c in enumerate(r) if c.isdigit() and len(c) == 11]
            if tc_d_indices:
                tc_d_idx = tc_d_indices[0]
                if tc_d_idx > tc_h_idx:
                    raw_rows[0] = [''] * (tc_d_idx - tc_h_idx) + raw_rows[0]

        max_len = max(len(r) for r in raw_rows)
        padded_rows = [r + [''] * (max_len - len(r)) for r in raw_rows]
        return pd.DataFrame(padded_rows)

    @staticmethod
    def mebbis_gorevlendirme_mi(dosya_yolu_veya_df):
        """Dosyanın veya metnin MEBBİS Görevlendirme Personel Tablosu olup olmadığını tespit eder."""
        try:
            import os
            if isinstance(dosya_yolu_veya_df, pd.DataFrame):
                df = dosya_yolu_veya_df
            elif isinstance(dosya_yolu_veya_df, str) and not os.path.exists(dosya_yolu_veya_df):
                df = ExcelMotoru.pano_metnini_tabloya_cevir(dosya_yolu_veya_df)
            else:
                df = ExcelMotoru.tabloyu_guvenli_oku(dosya_yolu_veya_df, header=None, dtype=str)
            if df.empty:
                return False
            tum_metin = " ".join([str(c) for c in df.columns]).upper()
            for idx in range(min(15, len(df))):
                satir = " ".join([str(x) for x in df.iloc[idx].values if pd.notna(x)])
                tum_metin += " " + satir.upper()
            if "AY.DER/KAD" in tum_metin or "AY.DER" in tum_metin or ("İSTİHDAM TİPİ" in tum_metin and "KADRO" in tum_metin) or ("GÖREV YERİ" in tum_metin and "KADRO" in tum_metin) or ("GÖREVLENDİRME" in tum_metin and "KADRO" in tum_metin):
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def _mebbis_tablo_ayristir(df, varsayilan_grup="Görevlendirme"):
        """
        MEBBİS veya Excel'den kopyalanan tablo halindeki personel verilerini (web panosu veya Excel)
        sütun adlarını esnek tespit ederek standart 24 alana dönüştürür.
        """
        import re
        from araclar import VeriAraclari
        from utils import _personel_grup_tahmin_et

        if df.empty:
            return []

        # Başlık satırını bul
        header_idx = -1
        for i, row in df.iterrows():
            satir_metni = " ".join([str(x).upper() for x in row.values if pd.notna(x)])
            if ("TC" in satir_metni or "T.C." in satir_metni or "KİMLİK" in satir_metni or "KIMLIK" in satir_metni) and \
               ("AD" in satir_metni or "SOYAD" in satir_metni or "AY.DER" in satir_metni or "UNVAN" in satir_metni or "ÜNVAN" in satir_metni or "BRANŞ" in satir_metni or "GÖREV" in satir_metni or "İSTİHDAM" in satir_metni):
                header_idx = i
                break

        if header_idx == -1:
            # Belirgin başlık bulunamadıysa ilk satırı dene
            header_idx = 0

        header_row = df.iloc[header_idx].values
        df_veri = df.iloc[header_idx + 1:].copy()
        col_names = []
        counts = {}
        for idx, x in enumerate(header_row):
            name = str(x).strip() if pd.notna(x) and str(x).strip() else f"col_{idx}"
            if name in counts:
                counts[name] += 1
                col_names.append(f"{name}_{counts[name]}")
            else:
                counts[name] = 1
                col_names.append(name)
        df_veri.columns = col_names

        def _bul(desenler, excludes=[]):
            for p in desenler:
                for col in df_veri.columns:
                    col_l = str(col).lower()
                    if any(ex in col_l for ex in excludes):
                        continue
                    if p.lower() in col_l:
                        return col
            return None

        c_tc = _bul(['TC Kimlik No', 'TC Kimlik', 'TC No', 'T.C. Kimlik No', 'T.C. No', 'T.C.', 'TC', 'Kimlik No', 'Kimlik'])
        c_ad = _bul(['Adı', 'Adi', 'Ad'], excludes=['baba', 'soy', 'kurum', 'okul', 'yer'])
        c_soyad = _bul(['Soyadı', 'Soyadi', 'Soyad'])
        c_ad_soyad = _bul(['Ad Soyad', 'Adı Soyadı', 'Adi Soyadi', 'Personel Adı', 'Personel'])
        c_kariyer = _bul(['Öğretmenlik Kariyer Basamağı', 'Kariyer Basamağı', 'Kariyer'])
        c_kademe = _bul(['Ay.Der/Kad', 'Der/Kad', 'Derece / Kademe', 'Kadro Derece', 'Derece', 'Kademe', 'Kazanılmış Hak'])
        c_sicil_em = _bul(['Emekli Sicil No', 'Emekli Sicil', 'Emekli', 'SGK No'])
        c_sicil_kurum = _bul(['Kurum Sicil No', 'Kurum Sicil', 'Sicil No', 'Sicil'])
        c_unvan = _bul(['Kadro Ünvanı', 'Kadro Unvanı', 'Kadro Unvani', 'Ünvan', 'Unvan', 'Kadro'])
        c_gorev = _bul(['Görevi', 'Gorevi', 'Görev', 'Gorev'], excludes=['yeri', 'il', 'kurum'])
        c_brans = _bul(['Alanı', 'Alani', 'Alan', 'Branşı', 'Bransı', 'Branş', 'Brans'])
        c_yer = _bul(['Görev Yeri', 'Gorev Yeri', 'Kurum Adı', 'Kurum', 'Okul Adı', 'Okul'])
        c_il = _bul(['İli', 'Ili', 'İl', 'Il'])
        c_ilce = _bul(['İlçesi', 'Ilcesi', 'İlçe', 'Ilce'])
        c_cinsiyet = _bul(['Cinsiyeti', 'Cinsiyet'])
        c_arsiv = _bul(['Arşiv No', 'Arsiv No', 'Arşiv', 'Arsiv'])
        c_durum = _bul(['Durumu', 'Durum', 'Statü Durumu', 'Aktif'])
        c_dogum = _bul(['Doğum Yılı', 'Dogum Yili', 'Doğum Tarihi', 'Dogum Tarihi'])
        c_grup = _bul(['Grup / Statü', 'Grup', 'İstihdam Tipi', 'İstihdam Türü', 'Statü', 'Personel Türü'])

        personeller = []
        for _, row in df_veri.iterrows():
            if c_ad and c_soyad:
                adi = str(row[c_ad]).strip() if pd.notna(row[c_ad]) else ''
                soyadi = str(row[c_soyad]).strip() if pd.notna(row[c_soyad]) else ''
                ad_soyad = f"{adi} {soyadi}".strip()
            elif c_ad_soyad:
                ad_soyad = str(row[c_ad_soyad]).strip() if pd.notna(row[c_ad_soyad]) else ''
            elif c_ad:
                ad_soyad = str(row[c_ad]).strip() if pd.notna(row[c_ad]) else ''
            else:
                continue

            if not ad_soyad or ad_soyad.lower() in ['nan', 'none', '-', '']:
                continue

            # Türkçe isim formatlama: İlk kelimeler ilk harf büyük, son kelime (soyad) tamamen BÜYÜK
            ad_soyad = VeriAraclari.tr_format_ad_soyad(ad_soyad)

            tc = str(row[c_tc]).strip() if (c_tc and pd.notna(row[c_tc])) else ''
            if tc.endswith('.0') and tc[:-2].isdigit(): tc = tc[:-2]
            if tc.lower() in ['nan', 'none']: tc = ''

            kademe_val = row[c_kademe] if (c_kademe and pd.notna(row[c_kademe])) else '-'
            kademe_derece = ExcelMotoru.akilli_kademe_derece(kademe_val)

            unvan = str(row[c_unvan]).strip() if (c_unvan and pd.notna(row[c_unvan])) else '-'
            if unvan.lower() in ['nan', 'none', '']: unvan = '-'

            gorev = str(row[c_gorev]).strip() if (c_gorev and pd.notna(row[c_gorev])) else '-'
            if gorev.lower() in ['nan', 'none', '']: gorev = unvan if unvan != '-' else '-'

            brans = str(row[c_brans]).strip() if (c_brans and pd.notna(row[c_brans])) else '-'
            if brans.lower() in ['nan', 'none', '']: brans = '-'

            kariyer = str(row[c_kariyer]).strip() if (c_kariyer and pd.notna(row[c_kariyer])) else '-'
            if kariyer.lower() in ['nan', 'none', '']: kariyer = '-'

            kurum_adi = str(row[c_yer]).strip() if (c_yer and pd.notna(row[c_yer])) else ''
            if kurum_adi.lower() in ['nan', 'none']: kurum_adi = ''

            il = str(row[c_il]).strip() if (c_il and pd.notna(row[c_il])) else ''
            ilce = str(row[c_ilce]).strip() if (c_ilce and pd.notna(row[c_ilce])) else ''
            if il.lower() in ['nan', 'none']: il = ''
            if ilce.lower() in ['nan', 'none']: ilce = ''
            il_ilce = f"{il} / {ilce}".strip(" /") if (il or ilce) else ''

            cins_raw = str(row[c_cinsiyet]).strip().upper() if (c_cinsiyet and pd.notna(row[c_cinsiyet])) else ''
            cinsiyet = 'E' if 'ERK' in cins_raw or cins_raw == 'E' else ('K' if 'KAD' in cins_raw or cins_raw == 'K' else '')

            arsiv_no = str(row[c_arsiv]).strip() if (c_arsiv and pd.notna(row[c_arsiv])) else ''
            if arsiv_no.lower() in ['nan', 'none']: arsiv_no = ''

            emekli_sicil = str(row[c_sicil_em]).strip() if (c_sicil_em and pd.notna(row[c_sicil_em])) else ''
            if emekli_sicil.endswith('.0') and emekli_sicil[:-2].isdigit(): emekli_sicil = emekli_sicil[:-2]
            if emekli_sicil.lower() in ['nan', 'none']: emekli_sicil = ''

            kurum_sicil = str(row[c_sicil_kurum]).strip() if (c_sicil_kurum and pd.notna(row[c_sicil_kurum])) else ''
            if kurum_sicil.endswith('.0') and kurum_sicil[:-2].isdigit(): kurum_sicil = kurum_sicil[:-2]
            if kurum_sicil.lower() in ['nan', 'none']: kurum_sicil = ''

            durum_raw = str(row[c_durum]).strip().lower() if (c_durum and pd.notna(row[c_durum])) else ''
            aktif = 0 if any(k in durum_raw for k in ['ayrıl', 'pasif', 'hayır', 'hayir']) else 1

            dogum = str(row[c_dogum]).strip() if (c_dogum and pd.notna(row[c_dogum])) else ''
            if dogum.endswith('.0') and dogum[:-2].isdigit(): dogum = dogum[:-2]
            if dogum.lower() in ['nan', 'none']: dogum = ''

            # Grup belirleme
            if varsayilan_grup == 'Görevlendirme':
                grup = 'Görevlendirme'
            elif varsayilan_grup == 'Kadrolu':
                grup_raw = str(row[c_grup]).strip() if (c_grup and pd.notna(row[c_grup])) else ''
                if grup_raw and grup_raw.lower() not in ['nan', 'none', '-', '']:
                    grup = grup_raw
                else:
                    grup = _personel_grup_tahmin_et(f"{unvan} {gorev}") or 'Kadrolu'
            else:
                grup_raw = str(row[c_grup]).strip() if (c_grup and pd.notna(row[c_grup])) else ''
                grup = grup_raw if (grup_raw and grup_raw.lower() not in ['nan', 'none', '-', '']) else varsayilan_grup

            personeller.append({
                'ad_soyad': ad_soyad,
                'tc_no': tc,
                'unvan': unvan,
                'brans': brans,
                'gorev': gorev,
                'grup': grup,
                'il_ilce': il_ilce,
                'kurum_adi': kurum_adi,
                'kurum_kodu': '',
                'kurumda_baslama': '',
                'kariyer': kariyer,
                'kademe_derece': kademe_derece,
                'ogrenim_durumu': '-',
                'cinsiyet': cinsiyet,
                'kan_grubu': '',
                'dogum_tarihi': dogum,
                'goreve_baslama': '',
                'kurum_sicil_no': kurum_sicil,
                'emekli_sicil_no': emekli_sicil,
                'arsiv_no': arsiv_no,
                'telefon': '',
                'eposta': '',
                'notlar': '',
                'aktif': aktif
            })

        return personeller

    @staticmethod
    def mebbis_gorevlendirme_personel_oku(kaynak):
        """
        MEBBİS Görevlendirme Çalışan Personel tablosunu (Excel dosyası veya kopyalanan pano metni/HTML)
        ayrıştırır ve her personeli standart 24 alana eşler.
        """
        import os

        if isinstance(kaynak, pd.DataFrame):
            df = kaynak
        elif isinstance(kaynak, str) and not os.path.exists(kaynak):
            df = ExcelMotoru.pano_metnini_tabloya_cevir(kaynak)
        else:
            df = ExcelMotoru.tabloyu_guvenli_oku(kaynak, header=None)

        if df.empty:
            return []

        return ExcelMotoru._mebbis_tablo_ayristir(df, varsayilan_grup="Görevlendirme")

    @staticmethod
    def mebbis_mi_kontrol_et(dosya_yolu):
        """Dosyanın MEBBİS Personel Listesi olup olmadığını tespit eder."""
        try:
            import re
            df = ExcelMotoru.tabloyu_guvenli_oku(dosya_yolu, header=None, dtype=str)
            if df.empty:
                return False
            for idx in range(min(30, len(df))):
                satir = " ".join([str(x) for x in df.iloc[idx].values if pd.notna(x)])
                if "PERSONEL LİSTESİ" in satir.upper() or "PERSONEL LISTESI" in satir.upper():
                    return True
                # Parantez içinde TC kimlik numarası kalıbı (AD SOYAD (12345678901))
                if re.search(r'\(\d{10,11}\)', satir):
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def mebbis_personel_oku(dosya_yolu):
        """
        MEBBİS'ten indirilen düzensiz, kayan satır/sütunlu 'Personel Listesi (Özet Bilgiler)'
        Excel dosyasını veya panodan yapıştırılan metni semantik kalıp tanıma (regex) yöntemiyle sıfır kayıpla ayrıştırır.
        """
        import os
        import io
        import re
        from araclar import VeriAraclari
        from utils import _personel_grup_tahmin_et

        if isinstance(dosya_yolu, pd.DataFrame):
            df = dosya_yolu
        elif isinstance(dosya_yolu, str) and not os.path.exists(dosya_yolu):
            df = ExcelMotoru.pano_metnini_tabloya_cevir(dosya_yolu)
        else:
            df = ExcelMotoru.tabloyu_guvenli_oku(dosya_yolu, header=None, dtype=str)

        if df.empty:
            return []

        re_kan = re.compile(r'\b(A|B|AB|0)\s*Rh\s*\([+-]\)', re.IGNORECASE)
        re_tarih_iso = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
        re_tarih_tr = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
        re_ogrenim = re.compile(r'(Lisans|Ön Lisans|Yüksek Lisans|Doktora|Ortaöğretim|İlköğretim)', re.IGNORECASE)
        re_kademe = re.compile(r'Görevde\s*(\d+[-/]\d+)', re.IGNORECASE)

        personeller = []
        current_person = None

        for idx, row in df.iterrows():
            row_cells = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != '']
            
            # Bu satır yeni bir personel başlangıcı mı? (AD SOYAD (TC))
            m_name_tc = None
            for cell in row_cells:
                m = re.search(r'([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*\((\d{10,11})\)', cell)
                if m and len(m.group(1).strip()) > 2:
                    m_name_tc = (m.group(1).strip(), m.group(2).strip(), cell)
                    break
                    
            if m_name_tc:
                if current_person:
                    personeller.append(current_person)
                ad_soyad, tc, raw_cell = m_name_tc
                current_person = {
                    'ad_soyad': VeriAraclari.tr_format_ad_soyad(ad_soyad),
                    'tc_no': tc,
                    'il_ilce': '',
                    'kurum_adi': '',
                    'kurum_kodu': '',
                    'kurumda_baslama': '',
                    'unvan': '-',
                    'gorev': '-',
                    'brans': '-',
                    'kariyer': '-',
                    'kademe_derece': '-',
                    'ogrenim_durumu': '-',
                    'kurum_sicil_no': '',
                    'emekli_sicil_no': '',
                    'arsiv_no': '',
                    'cinsiyet': '',
                    'kan_grubu': '',
                    'dogum_tarihi': '',
                    'goreve_baslama': '',
                    'telefon': '',
                    'eposta': '',
                    'notlar': '',
                    'grup': 'Kadrolu',
                    'raw_cells': list(row_cells)
                }
                row_items = [(c_idx, str(val).strip()) for c_idx, val in row.items() if pd.notna(val) and str(val).strip() != '']
                
                # 1. Kurum Bilgisi
                for c_idx, cell in row_items:
                    if '/' in cell and any(w in cell for w in ['Lisesi', 'Ortaokulu', 'İlkokulu', 'Kurumu', 'Müdürlüğü', 'Okulu', 'Merkezi']):
                        current_person['kurum_bilgi'] = cell
                        k_parts = [p.strip() for p in cell.split('/')]
                        current_person['kurum_adi'] = k_parts[0]
                        if len(k_parts) > 1: current_person['kurum_kodu'] = k_parts[1]
                        t_match = re_tarih_tr.search(cell)
                        if t_match:
                            current_person['kurumda_baslama'] = t_match.group(1)
                        break

                # 2. İl / İlçe
                for c_idx, cell in row_items:
                    if c_idx <= 2 and '/' in cell and cell != current_person.get('kurum_bilgi'):
                        if not re_tarih_tr.search(cell) and not re_tarih_iso.search(cell):
                            current_person['il_ilce'] = cell
                            break

                # 3. Unvan / Görev ve Branş / Kariyer (Sütun sırasına göre)
                slash_hucreleri = []
                for c_idx, cell in row_items:
                    if '/' in cell and cell != raw_cell and cell != current_person.get('kurum_bilgi') and cell != current_person.get('il_ilce'):
                        if not re_tarih_tr.search(cell) and not re_tarih_iso.search(cell):
                            slash_hucreleri.append((c_idx, cell))

                slash_hucreleri.sort(key=lambda x: x[0])

                if len(slash_hucreleri) >= 2:
                    ug_str = slash_hucreleri[0][1]
                    bk_str = slash_hucreleri[1][1]
                    
                    ug_parts = [p.strip() for p in ug_str.split('/')]
                    current_person['unvan'] = ug_parts[0] if ug_parts[0] else '-'
                    current_person['gorev'] = ug_parts[1] if (len(ug_parts) > 1 and ug_parts[1]) else current_person['unvan']

                    bk_parts = [p.strip() for p in bk_str.split('/')]
                    current_person['brans'] = bk_parts[0] if bk_parts[0] else '-'
                    current_person['kariyer'] = bk_parts[1] if (len(bk_parts) > 1 and bk_parts[1]) else '-'
                elif len(slash_hucreleri) == 1:
                    h_str = slash_hucreleri[0][1]
                    h_parts = [p.strip() for p in h_str.split('/')]
                    first = h_parts[0].upper()
                    if any(k in first for k in ['ÖĞRETMEN', 'MEMUR', 'MÜDÜR', 'VHKİ', 'HİZMETLİ', 'TEKNİSYEN', 'ŞEF']):
                        current_person['unvan'] = h_parts[0] if h_parts[0] else '-'
                        current_person['gorev'] = h_parts[1] if (len(h_parts) > 1 and h_parts[1]) else current_person['unvan']
                    else:
                        current_person['brans'] = h_parts[0] if h_parts[0] else '-'
                        current_person['kariyer'] = h_parts[1] if (len(h_parts) > 1 and h_parts[1]) else '-'
            elif current_person:
                current_person['raw_cells'].extend(row_cells)

        if current_person:
            personeller.append(current_person)

        if not personeller:
            # Pano veya standart tablo halindeki MEBBİS verisini sütun bazlı ayrıştır
            return ExcelMotoru._mebbis_tablo_ayristir(df, varsayilan_grup="Kadrolu")

        # Semantik zenginleştirme (Kayan sütunlardan bağımsız tip eşleme)
        for p in personeller:
            tarihler = []
            sayilar = []
            for cell in p['raw_cells']:
                kan_m = re_kan.search(cell)
                if kan_m:
                    p['kan_grubu'] = kan_m.group(0)
                elif cell in ['E', 'K']:
                    p['cinsiyet'] = cell
                elif 'Görevde' in cell:
                    kad_m = re_kademe.search(cell)
                    p['kademe_derece'] = kad_m.group(1) if kad_m else cell.replace('Görevde', '').strip()
                elif re_ogrenim.search(cell):
                    p['ogrenim_durumu'] = cell
                elif re_tarih_iso.search(cell):
                    tarihler.append(re_tarih_iso.search(cell).group(1))
                elif cell.isdigit() and 3 <= len(cell) <= 9 and cell != p['tc_no']:
                    sayilar.append(cell)
                elif re.match(r'^[A-Z0-9\-]{2,7}$', cell) and cell not in ['E', 'K', 'AB', 'A', 'B', '0'] and not p['arsiv_no']:
                    p['arsiv_no'] = cell

            if len(tarihler) >= 2:
                tarihler_sorted = sorted(tarihler)
                p['dogum_tarihi'] = tarihler_sorted[0]
                p['goreve_baslama'] = tarihler_sorted[1]
            elif len(tarihler) == 1:
                p['dogum_tarihi'] = tarihler[0]
                
            if len(sayilar) == 1:
                p['kurum_sicil_no'] = sayilar[0]
            elif len(sayilar) >= 2:
                p['kurum_sicil_no'] = sayilar[0]
                p['emekli_sicil_no'] = sayilar[1]
            if len(sayilar) >= 3 and not p['arsiv_no']:
                p['arsiv_no'] = sayilar[2]

            p['grup'] = _personel_grup_tahmin_et(f"{p['unvan']} {p['gorev']}")
            p.pop('raw_cells', None)

        return personeller
