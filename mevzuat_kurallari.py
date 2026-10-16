# =====================================================================
# MEVZUAT VE STATÜ BAZLI İŞ KURALLARI MOTORU (mevzuat_kurallari.py)
# =====================================================================
# Bu modül, MEB ve kamuda istihdam edilen tüm personel türlerinin tabi
# olduğu temel kanun, yönetmelik ve genelgeler doğrultusunda izin hakları,
# devamsızlık sınırları, çalışma saatleri ve yasal dayanaklarını tanımlar.
#
# Dayanak Mevzuatlar:
# 1. 657 sayılı Devlet Memurları Kanunu (Öğretmenler, Memurlar, VHKİ)
# 2. 4857 sayılı İş Kanunu (Kamuda 4/D Sürekli İşçiler)
# 3. 4904 sayılı İŞKUR Kanunu ve TYP Yönetmeliği (Toplum Yararına Programlar)
# 4. İŞKUR İşgücü Uyum Programı (İUP) Genelgesi ve Yönetmeliği
# 5. MEB İzin Yönergesi ve Milli Eğitim Temel Kanunu
# =====================================================================

from typing import Dict, Any, Optional

MEVZUAT_MATRISI: Dict[str, Dict[str, Any]] = {
    "Kadrolu": {
        "statu_adi": "657 Sayılı Kadrolu Personel (Öğretmen / Memur)",
        "kanun": "657 Sayılı Devlet Memurları Kanunu",
        "ogretmen_varsayilan": True,
        "ogretmen_kurallari": {
            "izin_hakki": "Yaz ve dinlenme tatillerinde izinli sayılır (Md. 103). Yıllık izin hakkı yoktur.",
            "mazeret_izni": "Babalık 10 gün, Evlilik 7 gün, Vefat 7 gün, Analık 16 hafta (Md. 104).",
            "hastalik_izni": "Hizmeti 10 yıla kadar 12 ay, 10 yıldan fazla 18 ay (Md. 105).",
            "devamsizlik_yaptirimi": "Özürsüz 1-2 gün: Aylıktan kesme (Md. 125/C); 3-9 gün: Kademe ilerlemesi durdurma (Md. 125/D); Kesintisiz 10 gün: Çekilmiş (müstafi) sayılma (Md. 94).",
            "brans_kariyer_var_mi": True,
            "kademe_derece_var_mi": True,
        },
        "memur_kurallari": {
            "izin_hakki": "Hizmeti 1-10 yıl olanlar için 20 gün; 10 yıldan fazla olanlar için 30 gün (Md. 102).",
            "mazeret_izni": "Babalık 10 gün, Evlilik 7 gün, Vefat 7 gün, Analık 16 hafta (Md. 104).",
            "hastalik_izni": "Hizmeti 10 yıla kadar 12 ay, 10 yıldan fazla 18 ay (Md. 105).",
            "devamsizlik_yaptirimi": "Özürsüz 1-2 gün: Aylıktan kesme; 3-9 gün: Kademe ilerlemesi durdurma; Kesintisiz 10 gün: Çekilmiş sayılma.",
            "brans_kariyer_var_mi": False,
            "kademe_derece_var_mi": True,
        },
        "aciklama": "Kadrolu personelde branş ve kariyer basamağı yalnızca öğretmen unvanlı personelde geçerlidir."
    },
    "Görevlendirme": {
        "statu_adi": "Geçici Görevlendirmeli Personel",
        "kanun": "657 Sayılı DMK Ek Madde 8 / MEB Görevlendirme Yönetmeliği",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Asıl kadrosunun tabi olduğu mevzuat hükümleri geçerlidir.",
        "brans_kariyer_var_mi": True,
        "kademe_derece_var_mi": True,
        "aciklama": "Kurumda fiilen görev yapan veya başka kuruma görevlendirilen personeldir."
    },
    "Sözleşmeli": {
        "statu_adi": "657 Sayılı Kanun Madde 4/B Sözleşmeli Personel",
        "kanun": "657 Sayılı DMK Madde 4/B ve Sözleşmeli Personel Çalıştırılmasına İlişkin Esaslar",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Hizmeti 1-10 yıl: 20 gün; 10 yıldan fazla: 30 gün. Sözleşmeli öğretmenler tatilde izinli sayılır.",
        "mazeret_izni": "Doğum 16 hafta, babalık 10 gün, evlilik 7 gün, vefat 7 gün.",
        "devamsizlik_yaptirimi": "Mazeretsiz kesintisiz 3 iş günü veya bir sözleşme döneminde 10 iş günü devamsızlıkta sözleşme feshedilir.",
        "brans_kariyer_var_mi": True,
        "kademe_derece_var_mi": True,
        "aciklama": "Sözleşmeli öğretmenlerde branş esastır; kariyer basamağı kadroya geçiş sonrası uygulanır."
    },
    "Ücretli": {
        "statu_adi": "Ek Ders Karşılığı Ücretli Öğretmen",
        "kanun": "657 Sayılı DMK Madde 89 / MEB Yönetici ve Öğretmenlerin Ders ve Ek Ders Saatlerine İlişkin Karar",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Yıllık veya mazeret izin hakkı yoktur. Girilmeyen dersler için ek ders ücreti ve SGK primi ödenmez.",
        "brans_kariyer_var_mi": True,
        "kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Ders saati bazlı görev yaparlar; kariyer basamağı ve kademe/derece bulunmaz."
    },
    "Sürekli İşçi": {
        "statu_adi": "4857 Sayılı İş Kanunu Kapsamında Sürekli İşçi (4/D)",
        "kanun": "4857 Sayılı İş Kanunu ve Kamu Toplu İş Sözleşmesi",
        "ogretmen_varsayilan": False,
        "izin_hakki": "Kıdeme göre: 1-5 yıl: 14 gün; 5-15 yıl: 20 gün; 15 yıldan fazla: 26 gün (Md. 53). 18 yaş altı veya 50+ yaş en az 20 gün.",
        "mazeret_izni": "Evlilik 3 gün, Vefat 3 gün, Doğum (babalık) 5 gün, Engelli çocuk tedavisi 10 gün (Ek Md. 2).",
        "devamsizlik_yaptirimi": "İşverenden izin almaksızın veya haklı sebebe dayanmaksızın ardı ardına 2 işgünü veya bir ayda tatil sonrası 2 işgünü ya da bir ayda 3 işgünü devamsızlık durumunda haklı fesih (Md. 25/II-g).",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Branş, öğretmenlik kariyeri veya memuriyet derecesi uygulanmaz; SGK sicili ve meslek kodu esastır."
    },
    "TYP": {
        "statu_adi": "Toplum Yararına Program Katılımcısı (TYP)",
        "kanun": "4904 Sayılı İŞKUR Kanunu ve TYP Yönetmeliği",
        "ogretmen_varsayilan": False,
        "calisma_duzeni": "Tam zamanlı (haftalık 45 saat), asgari ücret düzeyinde ödeme. Azami program süresi 9 aydır.",
        "izin_hakki": "Hafta tatili ve resmi tatiller hariç en fazla 5 güne kadar ÜCRETSİZ mazeret izni (Md. 11).",
        "devamsizlik_yaptirimi": "Herhangi bir nedenle 5 günlük izin süresinin aşılması halinde İLİŞİĞİ DERHAL KESİLİR (Md. 11/4).",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Kariyer, branş veya kademe yoktur. İzinli günlerde ücret ve sigorta primi ödenmez."
    },
    "İUP": {
        "statu_adi": "İşgücü Uyum Programı Katılımcısı (İUP)",
        "kanun": "İŞKUR İşgücü Uyum Programının Yürütülmesine İlişkin Usul ve Esaslar Genelgesi",
        "ogretmen_varsayilan": False,
        "calisma_duzeni": "Yarı zamanlı: Haftada 3 gün / 22.5 saat (ilk 4 hafta uyum için haftada 5 gün / 37.5 saat). Toplam en fazla 140 fiili gün.",
        "izin_hakki": "Program süresi 6 aya kadar ise en fazla 7 gün; 6 aydan uzun ise en fazla 10 gün izin (Genelge Md. 23).",
        "devamsizlik_yaptirimi": "Yüklenicinin (okulun) bilgi ve onayı olmadan veya belgeye dayalı mücbir neden olmaksızın 1 GÜN BİLE devamsızlık yapılması durumunda İLİŞİĞİ DERHAL KESİLİR (Genelge Md. 23/2 ve 15.6).",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Günlük cep harçlığı ve kısa vadeli SGK primi ödenir. İzin ve rapor günlerinde cep harçlığı verilmez."
    },
    "Hizmet Alımı": {
        "statu_adi": "Hizmet Alımı Personeli (Yüklenici Firma Personeli)",
        "kanun": "4734 Sayılı Kamu İhale Kanunu & 4857 Sayılı İş Kanunu",
        "ogretmen_varsayilan": False,
        "izin_hakki": "Yüklenici firmanın tabi olduğu 4857 sayılı İş Kanunu hükümleri geçerlidir.",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Özlük hakları ve izin süreçleri yüklenici firma tarafından yürütülür."
    }
}

# Öğretmen unvanları / anahtar kelimeleri
OGRETMEN_ANAHTARLAR = {
    "ÖĞRETMEN", "OGRETMEN", "MÜDÜR", "MUDUR", "MÜDÜR YARDIMCISI", "MUDUR YARDIMCISI",
    "MÜDÜR BAŞYARDIMCISI", "MUDUR BASYARDIMCISI", "UZMAN ÖĞRETMEN", "BAŞÖĞRETMEN"
}

# Açıkça öğretmen olmayan unvanlar
MEMUR_ISCI_ANAHTARLAR = {
    "MEMUR", "VHKİ", "V.H.K.İ.", "VERİ HAZIRLAMA", "HİZMETLİ", "HIZMETLI", "TEKNİSYEN",
    "TEKNIKER", "ŞEF", "SEF", "SÜREKLİ İŞÇİ", "SUREKLI ISCI", "İŞÇİ", "ISCI", "GÜVENLİK",
    "BEKÇİ", "AŞÇI", "ASCI", "ŞOFÖR", "SOFOR", "KALORİFERCİ", "TYP", "İUP", "IUP", "HİZMET ALIMI"
}


def ogretmen_mi(grup: Optional[str] = None, unvan: Optional[str] = None, gorev: Optional[str] = None) -> bool:
    """
    Personelin unvan, görev veya grubuna bakarak Öğretmen olup olmadığını tespit eder.
    Öğretmen değilse branş ve kariyer basamağı sorulmamalıdır.
    """
    grup_str = (grup or "").strip()
    unvan_str = (unvan or "").strip().upper().replace("İ", "I")
    gorev_str = (gorev or "").strip().upper().replace("İ", "I")

    # Kesinlikle öğretmen olmayan gruplar
    if grup_str in ["Sürekli İşçi", "TYP", "İUP", "Hizmet Alımı"]:
        return False

    # Unvan veya görev memur/işçi içeriyorsa öğretmen değildir
    for anahtar in MEMUR_ISCI_ANAHTARLAR:
        k = anahtar.replace("İ", "I")
        if k in unvan_str or k in gorev_str:
            return False

    # Unvan veya görev öğretmen içeriyorsa öğretmendir
    for anahtar in OGRETMEN_ANAHTARLAR:
        k = anahtar.replace("İ", "I")
        if k in unvan_str or k in gorev_str:
            return True

    # Belirtilmemişse grubun varsayılanına bak
    if grup_str in MEVZUAT_MATRISI:
        return bool(MEVZUAT_MATRISI[grup_str].get("ogretmen_varsayilan", False))

    return False


def mevzuat_bilgisi_al(grup: Optional[str] = None, unvan: Optional[str] = None) -> Dict[str, Any]:
    """
    Verilen grup veya unvana göre geçerli kanun maddelerini, izin haklarını
    ve devamsızlık uyarılarını döner.
    """
    grup_temiz = (grup or "Kadrolu").strip()
    matris_kaydi = MEVZUAT_MATRISI.get(grup_temiz, MEVZUAT_MATRISI["Kadrolu"])
    
    is_ogretmen = ogretmen_mi(grup=grup_temiz, unvan=unvan)
    
    sonuc = {
        "grup": grup_temiz,
        "ogretmen_mi": is_ogretmen,
        "kanun": matris_kaydi.get("kanun", ""),
        "statu_adi": matris_kaydi.get("statu_adi", ""),
        "brans_goster": is_ogretmen,
        "kariyer_goster": is_ogretmen and (grup_temiz != "Ücretli"),
        "kademe_derece_goster": grup_temiz in ["Kadrolu", "Görevlendirme", "Sözleşmeli"] and (not is_ogretmen or grup_temiz != "Ücretli"),
    }

    if grup_temiz == "Kadrolu":
        alt = matris_kaydi["ogretmen_kurallari"] if is_ogretmen else matris_kaydi["memur_kurallari"]
        sonuc.update(alt)
    else:
        for k, v in matris_kaydi.items():
            if k not in sonuc:
                sonuc[k] = v

    return sonuc


def devamsizlik_yaptirim_uyarisi(grup: str, mazeretsiz_gun: int) -> Optional[Dict[str, str]]:
    """
    Mazeretsiz devamsızlık gün sayısına göre mevzuatta öngörülen kritik yasal eşik uyarısını döner.
    """
    g = (grup or "").strip()
    if g == "İUP":
        if mazeretsiz_gun >= 1:
            return {
                "seviye": "KRİTİK",
                "mesaj": "İUP Genelgesi Md. 23/2 gereğince mazeretsiz 1 gün bile devamsızlık halinde İLİŞİK KESİLİR!",
                "yasal_dayanak": "İUP Genelgesi Madde 23 & 15.6"
            }
    elif g == "TYP":
        if mazeretsiz_gun > 5:
            return {
                "seviye": "KRİTİK",
                "mesaj": "TYP Yönetmeliği Md. 11/4 gereğince 5 günlük izin süresi aşıldığından İLİŞİK KESİLİR!",
                "yasal_dayanak": "TYP Yönetmeliği Madde 11/4"
            }
        elif mazeretsiz_gun >= 4:
            return {
                "seviye": "UYARI",
                "mesaj": f"TYP personeli toplam 5 gün izin hakkının {mazeretsiz_gun}. gününü doldurmak üzeredir.",
                "yasal_dayanak": "TYP Yönetmeliği Madde 11"
            }
    elif g == "Sürekli İşçi":
        if mazeretsiz_gun >= 3:
            return {
                "seviye": "KRİTİK",
                "mesaj": "4857 sayılı İş Kanunu Md. 25/II-g uyarınca 1 ayda 3 işgünü mazeretsiz devamsızlık HAKLI FESİH sebebidir.",
                "yasal_dayanak": "4857 Sayılı Kanun Madde 25/II-g"
            }
        elif mazeretsiz_gun >= 2:
            return {
                "seviye": "UYARI",
                "mesaj": "4857 sayılı İş Kanunu Md. 25/II-g uyarınca ardı ardına 2 işgünü devamsızlık fesih hakkı doğurur.",
                "yasal_dayanak": "4857 Sayılı Kanun Madde 25/II-g"
            }
    elif g in ["Kadrolu", "Görevlendirme"]:
        if mazeretsiz_gun >= 10:
            return {
                "seviye": "KRİTİK",
                "mesaj": "657 sayılı DMK Md. 94 gereğince kesintisiz 10 gün özürsüz göreve gelmeyen personel ÇEKİLMİŞ (müstafi) sayılır.",
                "yasal_dayanak": "657 DMK Madde 94"
            }
        elif mazeretsiz_gun >= 3:
            return {
                "seviye": "UYARI",
                "mesaj": "657 sayılı DMK Md. 125/D-b gereğince özürsüz 3-9 gün devamsızlık Kademe İlerlemesinin Durdurulması cezasını gerektirir.",
                "yasal_dayanak": "657 DMK Madde 125/D-b"
            }
        elif mazeretsiz_gun >= 1:
            return {
                "seviye": "BİLGİ",
                "mesaj": "657 sayılı DMK Md. 125/C-b gereğince özürsüz 1-2 gün göreve gelmemek Aylıktan Kesme cezasını gerektirir.",
                "yasal_dayanak": "657 DMK Madde 125/C-b"
            }
    return None

