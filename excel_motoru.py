import pandas as pd
import uuid
from araclar import VeriAraclari

class ExcelMotoru:
    @staticmethod
    def ogrenci_oku(dosya_yolu, mevcut_ogrenciler):
        yeni_liste = []
        try:
            # --- 1. GELİŞTİRME: Sahte XLS (HTML) Çözücü Zırhı ---
            try: df = pd.read_excel(dosya_yolu, header=None, dtype=str)
            except:
                try: 
                    df_list = pd.read_html(dosya_yolu, header=None, dtype=str)
                    df = max(df_list, key=len) if df_list else pd.DataFrame()
                except: df = pd.read_csv(dosya_yolu, header=None, dtype=str)

            aktif_sube = ""
            mevcut_nolar = {str(o['no']).strip() for o in mevcut_ogrenciler}
            yeni_nolar = set()
            
            for index, row in df.iterrows():
                satir_metni = str(row.values)
                if "Sınıf Listesi" in satir_metni:
                    aktif_sube = str(row[0]).split("Sınıf Listesi")[0].replace("Müdürlüğü", "").replace("\n", "").strip()
                    if "AL -" in aktif_sube: aktif_sube = aktif_sube.split("AL -")[-1].strip()
                elif pd.notna(row[1]) and str(row[1]).replace('.0', '').isdigit() and "Öğrenci" not in str(row[1]):
                    ogr_no = str(row[1]).replace('.0', '').strip()
                    ad = str(row[3]).strip() if pd.notna(row[3]) else ""
                    soyad = str(row[7]).strip() if pd.notna(row[7]) else ""
                    
                    if ad and soyad:
                        if ogr_no not in mevcut_nolar and ogr_no not in yeni_nolar:
                            yeni_liste.append({'no': ogr_no, 'ad_soyad': f"{ad} {soyad}".strip(), 'sube': aktif_sube})
                            yeni_nolar.add(ogr_no)
            return yeni_liste, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def devamsizlik_oku(dosya_yolu, mevcut_devamsizliklar):
        import uuid
        import pandas as pd
        from araclar import VeriAraclari
        
        yeni_liste = []
        eklenen = 0
        try:
            try: df = pd.read_excel(dosya_yolu, header=None, dtype=str)
            except:
                try: 
                    df_list = pd.read_html(dosya_yolu, header=None, dtype=str)
                    df = max(df_list, key=len) if df_list else pd.DataFrame()
                except: df = pd.read_csv(dosya_yolu, header=None, dtype=str)
            
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
