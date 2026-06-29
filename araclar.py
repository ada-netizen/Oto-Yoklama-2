import re
from datetime import datetime, timedelta

class VeriAraclari:
    @staticmethod
    def temiz_sure(sure_degeri):
        s = str(sure_degeri).strip()
        return s[:-2] if s.endswith(".0") else s

    @staticmethod
    def kisa_sube_adi(sube_str):
        s = str(sube_str)
        # Okul türü öneklerini (AL -, AMP - vb.) temizler
        s = re.sub(r'^[A-Z]+\s*-\s*', '', s)
        s = re.sub(r'\(.*?\)', '', s)
        # Sınıf ve şube kelimelerini atar
        s = s.replace(". Sınıf", "").replace(" Sınıf", "").replace("Sınıfı", "")
        s = s.replace("Şubesi", "").replace("Şube", "").replace("şubesi", "")
        # "10/A" veya "10 /A" gibi formatları her zaman nizami "10 / A" yapar
        if "/" in s:
            kisimlar = s.split("/")
            if len(kisimlar) == 2:
                s = f"{kisimlar[0].strip()} / {kisimlar[1].strip()}"
        return s.strip()
    
    @staticmethod
    def tarih_formatla(tarih_str):
        tarih_str = str(tarih_str).strip().replace(" 00:00:00", "").replace(".", "/").replace("-", "/")
        parts = tarih_str.split("/")
        if len(parts) == 3:
            if len(parts[0]) == 4: return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
            elif len(parts[2]) == 4: return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
        return tarih_str

    @staticmethod
    def excel_tarih_cevir(excel_tarih):
        try:
            gun_sayisi = float(excel_tarih)
            if gun_sayisi > 30000: return (datetime(1899, 12, 30) + timedelta(days=gun_sayisi)).strftime("%d/%m/%Y")
        except: pass
        return VeriAraclari.tarih_formatla(excel_tarih)

    @staticmethod
    def parse_tarih(t_str):
        try: return datetime.strptime(t_str, "%d/%m/%Y")
        except: return None

    @staticmethod
    def tr_upper(metin): 
        return metin.replace("i", "İ").replace("ı", "I").upper()

    @staticmethod
    def hesapla_devamsizlik(ogr_no, devamsizlik_listesi, gecici_devamsizliklar):
        from datetime import datetime, timedelta
        ozsz_toplam_net = 0.0
        ozrl_toplam_net = 0.0
        g_sayisi = 0 
        ogr_no_str = str(ogr_no).strip()
        
        for dev in devamsizlik_listesi + gecici_devamsizliklar:
            if str(dev['no']).strip() == ogr_no_str:
                tur = dev['tur'].upper()
                
                try: gun_miktari = float(VeriAraclari.temiz_sure(dev['gun']))
                except: gun_miktari = 0.0
                
                hi_miktari = 0.0

                try:
                    d, m, y = map(int, VeriAraclari.tarih_formatla(dev['tarih']).split('/'))
                    g_tarih = datetime(y, m, d)
                    
                    kalan_gun = gun_miktari
                    while kalan_gun > 0:
                        is_hafta_ici = g_tarih.weekday() < 5
                        dusulecek = 1.0 if kalan_gun >= 1 else kalan_gun
                        
                        if is_hafta_ici:
                            hi_miktari += dusulecek
                            
                        kalan_gun -= dusulecek
                        g_tarih += timedelta(days=1)
                except: 
                    hi_miktari = gun_miktari
                
                # Yıllık tablo ile %100 aynı kategori dağılımı
                if tur in ["D", "ÖY", "SY"]: 
                    ozsz_toplam_net += hi_miktari
                elif tur == "G":
                    g_sayisi += 1 
                elif tur in ["N", "F", "SV"]: 
                    pass 
                else: 
                    ozrl_toplam_net += hi_miktari

        if g_sayisi > 0:
            ozsz_toplam_net += (g_sayisi // 5) * 0.5
            
        return ozsz_toplam_net, ozrl_toplam_net
