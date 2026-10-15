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
