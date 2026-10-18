# =====================================================================
# MEVZUAT VE STATÜ BAZLI İŞ KURALLARI MOTORU (mevzuat_kurallari.py)
# =====================================================================
# Bu modül, MEB ve kamuda istihdam edilen tüm personel türlerinin tabi
# olduğu temel kanun, yönetmelik ve genelgeler doğrultusunda izin hakları,
# devamsızlık sınırları, çalışma saatleri, kariyer basamakları ve yasal
# dayanaklarını tanımlar.
#
# Program klasöründeki resmi "mevzuat/" kütüphanesi referans alınmıştır:
# 1. 657 sayılı Devlet Memurları Kanunu (1.5.657.pdf)
# 2. 7528 sayılı Öğretmenlik Mesleği Kanunu & Kariyer Basamakları (7.5.41110.pdf)
# 3. 1739 sayılı Millî Eğitim Temel Kanunu (08144011_KANUN.pdf)
# 4. 4857 sayılı İş Kanunu (1.5.4857.pdf) - 4/D Sürekli İşçiler
# 5. 4904 sayılı İŞKUR Kanunu ve TYP Yönetmeliği (1.5.4904.pdf)
# 6. İŞKUR İşgücü Uyum Programı (İUP) Genelgesi ve Yönetmeliği
# 7. MEB Ortaöğretim Kurumları Yönetmeliği (7.5.18812.pdf - 22/2/2025/32821 RG)
# 8. MEB Eğitim Kurumları Yönetici Görevlendirme Yönetmeliği (7.5.44989.pdf)
# 9. MEB Sözleşmeli Öğretmen İstihdamına İlişkin Yönetmelik (7.5.41250.pdf)
# 10. MEB Personelinin Görevde Yükselme ve Unvan Değişikliği (7.5.18945.pdf)
# 11. 375 sayılı Kanun Hükmünde Kararname (4.5.375.pdf)
# 12. MEB Özel Eğitim Hizmetleri Yönetmeliği (7.5.24736.pdf)
# 13. MEB Sosyal Etkinlikler Yönetmeliği (7.5.23639.pdf)
# 14. MEB Okul-Aile Birliği Yönetmeliği (7.5.15878.pdf)
# 15. MEB Pansiyonlar ve Yatılılık Yönetmeliği (21.5.20169487.pdf)
# =====================================================================

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

# =====================================================================
# 1. RESMİ MEVZUAT KÜTÜPHANESİ ENVANTERİ
# =====================================================================
DAYANAK_MEVZUAT_ENVANTERI: Dict[str, Dict[str, str]] = {
    "657_SK": {
        "ad": "657 Sayılı Devlet Memurları Kanunu",
        "dosya": "mevzuat/1.5.657.pdf",
        "kapsam": "Memur ve kadrolu öğretmenlerin statüleri, izin, disiplin ve özlük hakları",
        "onemli_maddeler": "Md. 88 (İkinci Görev), Md. 89 (Ek Ders), Md. 94 (Çekilmiş Sayılma), Md. 102 (Yıllık İzin), Md. 103 (Öğretmen Tatili), Md. 104 (Mazeret İzinleri), Md. 105 (Hastalık ve Refakat), Md. 108 (Aylıksız İzin), Md. 125 (Disiplin Cezaları)"
    },
    "7528_SK": {
        "ad": "7528 Sayılı Öğretmenlik Mesleği Kanunu",
        "dosya": "mevzuat/7.5.41110.pdf",
        "kapsam": "Öğretmenlik mesleği kariyer basamakları (Uzman ve Başöğretmenlik), hak ve sorumluluklar",
        "onemli_maddeler": "Kariyer basamakları, her unvan için +1 derece verilmesi (Md. 18/3), yöneticilik ikinci görev (Md. 21)"
    },
    "1739_SK": {
        "ad": "1739 Sayılı Millî Eğitim Temel Kanunu",
        "dosya": "mevzuat/08144011_KANUN.pdf",
        "kapsam": "Türk Millî Eğitiminin temel ilkeleri, eğitim hakkı, öğretmenlik mesleği ve okul devam zorunluluğu",
        "onemli_maddeler": "Md. 26 (Okula Devam Mecburiyeti), Md. 43-45 (Öğretmenlik ve Yönetici Görevleri)"
    },
    "4857_SK": {
        "ad": "4857 Sayılı İş Kanunu",
        "dosya": "mevzuat/1.5.4857.pdf",
        "kapsam": "Kamuda 4/D statüsündeki sürekli işçiler, taşeron ve hizmet alımı personeli",
        "onemli_maddeler": "Md. 25/II-g (Devamsızlık Haklı Fesih), Md. 53 (Yıllık Ücretli İzin), Ek Md. 2 (Mazeret İzinleri)"
    },
    "4904_SK": {
        "ad": "4904 Sayılı Türkiye İş Kurumu Kanunu & TYP Yönetmeliği",
        "dosya": "mevzuat/1.5.4904.pdf",
        "kapsam": "Toplum Yararına Programlar (TYP) katılımcıları çalışma esasları",
        "onemli_maddeler": "TYP Yönetmeliği Md. 11 (Azami 5 gün ücretsiz mazeret izni ve aşımında derhal ilişik kesilme)"
    },
    "MEB_ORTAOGRETIM_YON": {
        "ad": "MEB Ortaöğretim Kurumları Yönetmeliği",
        "dosya": "mevzuat/7.5.18812.pdf",
        "kapsam": "Öğrenci devam-devamsızlık, geç kalma, veli tebligatları, izin ve sınıf geçme (22/2/2025 güncel)",
        "onemli_maddeler": "Md. 35 (5 Geç = 0.5 Gün Özürsüz), Md. 36/4 (5, 15, 25. gün tebligatları), Md. 36/5-a (10 gün özürsüz, 30 gün toplam), Md. 36/5-b (Özel durumlar: 40, 60, 70 gün sınırları), Md. 36/7 (5 iş günü özür belgesi süresi)"
    },
    "MEB_YONETICI_GOREVLENDIRME": {
        "ad": "MEB Eğitim Kurumları Yönetici Görevlendirme Yönetmeliği",
        "dosya": "mevzuat/7.5.44989.pdf",
        "kapsam": "Müdür, Müdür Başyardımcısı ve Müdür Yardımcısı görevlendirme ve hiyerarşisi",
        "onemli_maddeler": "Md. 6 (Müdürlük şartları), Md. 7 (Müdür yardımcılığı 2 yıl öğretmenlik şartı), Md. 25-26 (4+4=8 yıl süre), Md. 36 (Başyardımcılık geçişi)"
    },
    "MEB_SOZLESMELI_OGRETMEN": {
        "ad": "MEB Sözleşmeli Öğretmen İstihdamına İlişkin Yönetmelik",
        "dosya": "mevzuat/7.5.41250.pdf",
        "kapsam": "657 sayılı DMK 4/B sözleşmeli öğretmen hakları ve sözleşme fesih koşulları",
        "onemli_maddeler": "Md. 18 (3 yıl sonunda kadroya geçiş), Mazeretsiz kesintisiz 3 gün veya dönemde 10 gün devamsızlıkta fesih"
    },
    "MEB_GOREVDE_YUKSELME": {
        "ad": "MEB Personelinin Görevde Yükselme, Unvan Değişikliği ve Yer Değiştirme Yönetmeliği",
        "dosya": "mevzuat/7.5.18945.pdf",
        "kapsam": "Büro, teknik, sağlık ve yardımcı hizmetler kadroları görev ve yetkileri",
        "onemli_maddeler": "Şef, Memur, V.H.K.İ., Sayman, Bilgisayar İşletmeni, Teknisyen, Hizmetli sınıfları"
    }
}

# =====================================================================
# 2. STATÜ BAZLI MEVZUAT VE İZİN MATRİSİ
# =====================================================================
MEVZUAT_MATRISI: Dict[str, Dict[str, Any]] = {
    "Kadrolu": {
        "statu_adi": "657 Sayılı Kadrolu Personel (Öğretmen / Yönetici / Memur)",
        "kanun": "657 Sayılı DMK & 7528 Sayılı Öğretmenlik Mesleği Kanunu",
        "ogretmen_varsayilan": True,
        "ogretmen_kurallari": {
            "izin_hakki": "Yaz ve dinlenme tatillerinde izinli sayılır (657 SK Md. 103). Yıllık izin hakkı yoktur.",
            "mazeret_izni": "Analık: 16 hafta (8+8) (çoğulda 18 hafta); Babalık: 10 gün; Evlilik: 7 gün; Vefat: 7 gün (eş, çocuk, anne, baba, kardeş); Engelli çocuk tedavisi: yılda 10 gün; Süt izni: ilk 6 ay 3 saat, ikinci 6 ay 1.5 saat (Md. 104).",
            "hastalik_izni": "Kanser, verem ve akıl hastalığı gibi uzun süreli tedavilerde 18 aya kadar; diğer hastalıklarda 12 aya kadar izin verilir (sağlık kurulu raporuyla aynı süre kadar bir kez uzatılabilir) (657 SK Md. 105). Tek hekim tek seferde max 10 gün, yılda tek hekimden max 40 gün.",
            "refakat_izni": "Ağır kaza veya hayati tehlike halinde 3 aya kadar, lüzum görülürse +3 ay (toplam 6 ay) (Md. 105).",
            "ayliksiz_izin": "Analık sonrası 24 ay, askerlik süresince, 5 yıl hizmeti tamamlayana isteğiyle 1 yıla kadar (Md. 108).",
            "devamsizlik_yaptirimi": "Geç gelme/erken çıkma: Uyarma (Md. 125/A-b); Özürsüz 1-2 gün: Aylıktan kesme (Md. 125/C-b); Özürsüz 3-9 gün: Kademe ilerlemesi durdurma (Md. 125/D-b); Kesintisiz 10 gün: Çekilmiş (müstafi) sayılma (Md. 94); Yılda toplam 20 gün: Memurluktan çıkarma (Md. 125/E-d).",
            "brans_kariyer_var_mi": True,
            "kademe_derece_var_mi": True,
        },
        "memur_kurallari": {
            "izin_hakki": "Hizmeti 1-10 yıl olanlar için 20 gün; 10 yıldan fazla olanlar için 30 gün (657 SK Md. 102).",
            "mazeret_izni": "Analık: 16 hafta; Babalık: 10 gün; Evlilik: 7 gün; Vefat: 7 gün; Engelli çocuk: yılda 10 gün; Süt izni: ilk 6 ay 3 saat, ikinci 6 ay 1.5 saat (Md. 104).",
            "hastalik_izni": "Kanser, verem ve akıl hastalığı gibi uzun süreli tedavilerde 18 aya kadar; diğer hastalıklarda 12 aya kadar (sağlık kurulu raporuyla aynı süre kadar bir kez uzatılabilir) (657 SK Md. 105).",
            "refakat_izni": "3 aya kadar, gerekirse +3 ay (toplam 6 ay).",
            "ayliksiz_izin": "Doğum sonrası 24 ay, askerlik, 5 yıla 1 yıl (Md. 108).",
            "devamsizlik_yaptirimi": "Geç gelme: Uyarma; Özürsüz 1-2 gün: Aylıktan kesme; Özürsüz 3-9 gün: Kademe durdurma; Kesintisiz 10 gün: Çekilmiş sayılma (Md. 94); Yılda 20 gün: Çıkarma (Md. 125/E-d).",
            "brans_kariyer_var_mi": False,
            "kademe_derece_var_mi": True,
        },
        "aciklama": "Kadrolu personelde branş ve öğretmenlik kariyer basamağı yalnızca öğretmen ve eğitim kurumu yöneticilerinde uygulanır."
    },
    "Görevlendirme": {
        "statu_adi": "Geçici Görevlendirmeli Personel (Yönetici / Öğretmen / Memur)",
        "kanun": "657 Sayılı DMK Ek Madde 8 & MEB Yönetici Görevlendirme Yönetmeliği",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Asıl kadrosunun tabi olduğu mevzuat hükümleri geçerlidir. Kurum içi izin onayları görev yaptığı okul müdürlüğünce işlenir.",
        "brans_kariyer_var_mi": True,
        "kademe_derece_var_mi": True,
        "aciklama": "Kurumda fiilen görev yapan veya başka kuruma geçici görevlendirilen personeldir. Yöneticilik görevleri ikinci görev kapsamında yürütülür."
    },
    "Sözleşmeli": {
        "statu_adi": "657 Sayılı Kanun Madde 4/B Sözleşmeli Personel",
        "kanun": "657 Sayılı DMK Madde 4/B & MEB Sözleşmeli Öğretmen İstihdamına İlişkin Yönetmelik",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Hizmeti 1-10 yıl: 20 gün; 10 yıldan fazla: 30 gün. Sözleşmeli öğretmenler yaz ve ara tatillerde izinli sayılır.",
        "mazeret_izni": "Doğum 16 hafta, babalık 10 gün, evlilik 7 gün, vefat 7 gün, süt izni ilk 6 ay 3 saat, ikinci 6 ay 1.5 saat.",
        "kadroya_gecis": "3 yıllık çalışma süresini tamamlayan sözleşmeli öğretmenler talepleri halinde görev yaptıkları yerde öğretmen kadrolarına atanırlar (Md. 18).",
        "devamsizlik_yaptirimi": "Mazeretsiz kesintisiz 3 iş günü veya bir sözleşme döneminde toplam 10 iş günü devamsızlık durumunda hizmet sözleşmesi derhal feshedilir.",
        "brans_kariyer_var_mi": True,
        "kademe_derece_var_mi": True,
        "aciklama": "Sözleşmeli öğretmenlerde branş esastır; 3 yıl sonra kadroya geçiş hakkı mevcuttur."
    },
    "Ücretli": {
        "statu_adi": "Ek Ders Karşılığı Ücretli Öğretmen",
        "kanun": "657 Sayılı DMK Madde 89 & MEB Ders ve Ek Ders Saatlerine İlişkin Karar",
        "ogretmen_varsayilan": True,
        "izin_hakki": "Yıllık veya mazeret izin hakkı yoktur. Girilmeyen veya mazeretli dersler için ek ders ücreti ve SGK primi ödenmez.",
        "devamsizlik_yaptirimi": "Derse mazeretsiz gelinmediğinde ücret ödenmez; devamsızlığın devamı halinde görevlendirme okul yönetimince derhal iptal edilir.",
        "brans_kariyer_var_mi": True,
        "kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Ders saati bazlı görev yaparlar; kariyer basamağı ve kademe/derece bulunmaz."
    },
    "Sürekli İşçi": {
        "statu_adi": "4857 Sayılı İş Kanunu Kapsamında Sürekli İşçi (4/D)",
        "kanun": "4857 Sayılı İş Kanunu & Kamu Toplu İş Sözleşmesi (KHK 375)",
        "ogretmen_varsayilan": False,
        "izin_hakki": "Kıdeme göre yıllık ücretli izin: 1-5 yıl: 14 gün; 5-15 yıl: 20 gün; 15 yıldan fazla: 26 gün (4857 SK Md. 53). 18 yaş altı veya 50+ yaş için en az 20 gündür.",
        "mazeret_izni": "Evlilik: 3 gün; Vefat: 3 gün (ana, baba, eş, kardeş, çocuk); Babalık: 5 gün; Engelli çocuk tedavisi: 10 gün (Ek Md. 2).",
        "devamsizlik_yaptirimi": "İşverenden izin almaksızın veya haklı sebebe dayanmaksızın ardı ardına 2 işgünü veya bir ayda tatil sonrası 2 işgünü ya da bir ayda toplam 3 işgünü işe devam etmemek HAKLI NEDENLE BİLDİRİMSİZ DERHAL FESİH sebebidir (Md. 25/II-g).",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Branş, öğretmenlik kariyeri veya memuriyet derecesi uygulanmaz; SGK sicili, meslek kodu ve kıdem esastır."
    },
    "TYP": {
        "statu_adi": "Toplum Yararına Program Katılımcısı (TYP)",
        "kanun": "4904 Sayılı İŞKUR Kanunu ve TYP Yönetmeliği",
        "ogretmen_varsayilan": False,
        "calisma_duzeni": "Tam zamanlı (haftalık 45 saat), asgari ücret düzeyinde ödeme. Bir katılımcı için azami program süresi 9 aydır.",
        "izin_hakki": "Hafta tatili ve resmi tatiller hariç en fazla 5 güne kadar ÜCRETSİZ mazeret izni (TYP Yönetmeliği Md. 11).",
        "devamsizlik_yaptirimi": "Herhangi bir nedenle 5 günlük ücretsiz mazeret izni süresinin aşılması halinde İLİŞİĞİ DERHAL KESİLİR (Yönetmelik Md. 11/4).",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Kariyer, branş veya kademe yoktur. İzinli günlerde ücret ve sigorta primi ödenmez."
    },
    "İUP": {
        "statu_adi": "İşgücü Uyum Programı Katılımcısı (İUP)",
        "kanun": "İŞKUR İşgücü Uyum Programının Yürütülmesine İlişkin Usul ve Esaslar Genelgesi",
        "ogretmen_varsayilan": False,
        "calisma_duzeni": "Yarı zamanlı: Haftada 3 gün / 22.5 saat (ilk 4 hafta uyum eğitimi için haftada 5 gün / 37.5 saat). Bir kişi için toplam azami 140 fiili gündür.",
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
        "izin_hakki": "Yüklenici firmanın tabi olduğu 4857 sayılı İş Kanunu ve firma sözleşmesi hükümleri geçerlidir.",
        "brans_kariyer_var_mi": False,
        "kademe_derece_var_mi": False,
        "aciklama": "Özlük hakları ve izin süreçleri yüklenici firma tarafından yürütülür."
    }
}

# =====================================================================
# 3. ÖĞRETMEN VE MEMUR/İŞÇİ UNVAN ANAHTAR KELİMELERİ
# =====================================================================
OGRETMEN_ANAHTARLAR = {
    "ÖĞRETMEN", "OGRETMEN", "MÜDÜR", "MUDUR", "MÜDÜR YARDIMCISI", "MUDUR YARDIMCISI",
    "MÜDÜR BAŞYARDIMCISI", "MUDUR BASYARDIMCISI", "MÜDÜR YETKİLİ ÖĞRETMEN", "MUDUR YETKILI OGRETMEN",
    "UZMAN ÖĞRETMEN", "UZMAN OGRETMEN", "BAŞÖĞRETMEN", "BASOGRETMEN", "ADAY ÖĞRETMEN", "ADAY OGRETMEN"
}

MEMUR_ISCI_ANAHTARLAR = {
    "MEMUR", "VHKİ", "V.H.K.İ.", "VERİ HAZIRLAMA", "HİZMETLİ", "HIZMETLI", "TEKNİSYEN",
    "TEKNIKER", "ŞEF", "SEF", "SÜREKLİ İŞÇİ", "SUREKLI ISCI", "İŞÇİ", "ISCI", "GÜVENLİK",
    "BEKÇİ", "AŞÇI", "ASCI", "ŞOFÖR", "SOFOR", "KALORİFERCİ", "SAYMAN", "AYNİYAT SAYMANI",
    "BİLGİSAYAR İŞLETMENİ", "PROGRAMCI", "ÇÖZÜMLEYİCİ", "MÜHENDİS", "MİMAR", "DİYETİSYEN",
    "PSİKOLOG", "SOSYOLOG", "HEMŞİRE", "LABORANT", "VEZNEDAR", "AMBAR MEMURU", "SEKRETER",
    "USTA ÖĞRETİCİ", "MATBAACI", "TYP", "İUP", "IUP", "HİZMET ALIMI"
}

# =====================================================================
# 4. 7528 SAYILI KANUN KARİYER BASAMAKLARI VE YÖNETİCİ HİYERARŞİSİ
# =====================================================================
KARIYER_BASAMAKLARI_KURALLARI: Dict[str, Any] = {
    "kanun": "7528 Sayılı Öğretmenlik Mesleği Kanunu & Yönetmelik (7.5.41110.pdf)",
    "basamaklar": ["Aday Öğretmen", "Öğretmen", "Uzman Öğretmen", "Başöğretmen"],
    "uzman_ogretmenlik_sartlari": {
        "hizmet_suresi_yil": 10,
        "ceza_sarti": "Kademe ilerlemesinin durdurulması cezası bulunmamak (Md. 11/1-c)",
        "egitim_sarti": "Uzman Öğretmenlik Eğitim Programını tamamlamış olmak",
        "derece_artisi": "+1 Derece verilir (Md. 18/3)"
    },
    "basogretmenlik_sartlari": {
        "uzmanlikta_hizmet_suresi_yil": 10,
        "gecici_madde_istisnasi": "18/10/2024 tarihinde görevde bulunanlar öğretmenlikte 20 yılı doldurmuşsa uzmanlıkta 10 yıl şartı aranmaz (Geçici Md. 1)",
        "ceza_sarti": "Kademe ilerlemesinin durdurulması cezası bulunmamak (Md. 11/2-c)",
        "egitim_sarti": "Başöğretmenlik Eğitim Programını tamamlamış olmak",
        "derece_artisi": "+1 Derece verilir (Md. 18/3)"
    }
}

YONETICI_GOREVLERI_KURALLARI: Dict[str, Any] = {
    "kanun": "657 Sayılı DMK Md. 88, 7528 Sayılı Kanun Md. 21 & Yönetmelik (7.5.44989.pdf)",
    "nitelik": "Yöneticilik bir kadro değil, ikinci görev kapsamında yürütülür.",
    "hiyerarsi_ve_oncelik": [
        {"oncelik": 1, "unvan": "Müdür", "sart": "Yöneticilik yapmış olmak, 4+4 azami 8 ders yılı görev süresi"},
        {"oncelik": 2, "unvan": "Müdür Başyardımcısı", "sart": "Mevcut görev süresini dolduruncaya kadar devam eder (Md. 36/3)"},
        {"oncelik": 3, "unvan": "Müdür Yardımcısı", "sart": "Adaylık dahil en az 2 yıl öğretmenlik yapmış olmak (Md. 7), kadın ve alan önceliği"},
        {"oncelik": 4, "unvan": "Müdür Yetkili Öğretmen", "sart": "Müdür normu olmayan kurumlarda yönetim hizmetini yürütmek (Md. 32)"}
    ]
}

# =====================================================================
# 5. MEB ORTAÖĞRETİM KURUMLARI YÖNETMELİĞİ ÖĞRENCİ DEVAMSIZLIK KURALLARI
# =====================================================================
OGRENCI_MEVZUAT_KURALLARI: Dict[str, Any] = {
    "kanun": "1739 Sayılı Millî Eğitim Temel Kanunu (Md. 26)",
    "yonetmelik": "MEB Ortaöğretim Kurumları Yönetmeliği (Değişiklik: 22/2/2025 - 32821 RG)",
    "gec_kalma_kurali": {
        "oran": "5 Defa Geç Kalma = 0.5 Gün Özürsüz Devamsızlık (Md. 35/1)",
        "aciklama": "Geç gelme birinci ders saati için belirlenen süre ile sınırlıdır."
    },
    "yarim_gun_kurali": {
        "oran": "Günlük toplam ders saatinin 2/3'ü ve fazlasına gelmeyenlerin devamsızlığı 1 tam gün, daha azına gelmeyenler 0.5 gün sayılır (Md. 36/2-b)."
    },
    "genel_devamsizlik_sinirlari": {
        "ozursuz_azami": 10.0,
        "toplam_azami": 30.0,
        "yaptirim": "Ders puanları ne olursa olsun BAŞARISIZ sayılır ve sınıf tekrarı uygulanır (Md. 36/5-a)."
    },
    "tebligat_esikleri": {
        "standart_gunler": [5, 15, 25],
        "art_arda_gun": 2,
        "art_arda_kural": "Art arda 2 gün özürsüz devamsızlık yapan öğrencinin durumu velisine bildirilir ve veli okula davet edilir (Md. 36/4).",
        "komisyon_gorevi": "Önleme, Müdahale ve Yönlendirme Komisyonu devamsızlığın 5. gününde veliyi okula davet eder (Md. 36/5-a)."
    },
    "sosyal_sorumluluk_yaptirimi": "Özürsüz her 1 gün devamsızlık için sosyal sorumluluk çalışmalarına 1 saat eklenir (Md. 36/5-a).",
    "ozur_belgesi_suresi": {
        "standart_is_gunu": 5,
        "uzatilabilir_azami_is_gunu": 20,
        "aciklama": "Özür gününü takip eden en geç 5 iş günü içinde okul yönetimine veli tarafından verilir. Zorunlu hallerde okul yönetimince 20 iş gününe kadar uzatılabilir (Md. 36/7)."
    },
    "ozel_durum_sinirlari": {
        "vefat_1_derece": {
            "ad": "Birinci Dereceden Yakınını Kaybeden Öğrenciler",
            "ozursuz_azami": 10.0,
            "toplam_azami": 40.0,
            "dayanak": "Md. 36/5-b (22/2/2025 RG)"
        },
        "agir_tedavi_ve_koruma": {
            "ad": "Yatarak Tedavi, Organ Nakli, Koruma Altında ve Tutuklu Öğrenciler",
            "ozursuz_azami": 10.0,
            "toplam_azami": 60.0,
            "ek_tebligat_gunleri": [40, 55],
            "dayanak": "Md. 36/4 & Md. 36/5-b"
        },
        "kaynastirma_ve_ozel_egitim": {
            "ad": "Tam Zamanlı Kaynaştırma / Bütünleştirme ve Özel Eğitim Meslek Lisesi Öğrencileri",
            "ozursuz_azami": 20.0,
            "toplam_azami": 70.0,
            "ek_tebligat_gunleri": [40, 55],
            "dayanak": "Md. 36/4 & Md. 36/5-b"
        }
    }
}

# =====================================================================
# 6. YARDIMCI VE SORGULAMA FONKSİYONLARI
# =====================================================================

def ogretmen_mi(grup: Optional[str] = None, unvan: Optional[str] = None, gorev: Optional[str] = None) -> bool:
    """
    Personelin unvan, görev veya grubuna bakarak Öğretmen/Eğitimci olup olmadığını tespit eder.
    Öğretmen değilse branş ve kariyer basamağı sorulmamalıdır.
    """
    grup_str = (grup or "").strip()
    unvan_str = (unvan or "").strip().upper().replace("İ", "I")
    gorev_str = (gorev or "").strip().upper().replace("İ", "I")

    # Kesinlikle öğretmen olmayan gruplar
    if grup_str in ["Sürekli İşçi", "TYP", "İUP", "Hizmet Alımı"]:
        return False

    # Unvan veya görev açıkça memur/işçi içeriyorsa öğretmen değildir
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


def yonetici_mi(unvan: Optional[str] = None, gorev: Optional[str] = None) -> bool:
    """
    Personelin okul yöneticisi (Müdür, Müdür Başyardımcısı, Müdür Yardımcısı) olup olmadığını tespit eder.
    """
    metin = f"{unvan or ''} {gorev or ''}".strip().upper().replace("İ", "I")
    return any(y in metin for y in ["MUDUR", "MÜDÜR", "IDARECI", "İDARECİ"])


def yonetici_oncelik_sirasi(gorev: Optional[str] = None, unvan: Optional[str] = None) -> int:
    """
    Personel listesi hiyerarşik sıralamasında öncelik puanı döner:
    1: Okul Müdürü
    2: Müdür Başyardımcısı
    3: Müdür Yardımcısı
    4: Müdür Yetkili Öğretmen
    99: Diğer Personel
    """
    m = f"{gorev or ''} {unvan or ''}".strip().upper().replace("İ", "I")
    if "BASYARDIM" in m or "BAŞYARDIM" in m:
        return 2
    if "YARDIMCI" in m:
        return 3
    if "YETKILI" in m or "YETKİLİ" in m:
        return 4
    if "MUDUR" in m or "MÜDÜR" in m:
        return 1
    return 99


def mevzuat_bilgisi_al(grup: Optional[str] = None, unvan: Optional[str] = None) -> Dict[str, Any]:
    """
    Verilen grup veya unvana göre geçerli kanun maddelerini, izin haklarını,
    çalışma düzenini ve devamsızlık uyarılarını döner.
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
                "mesaj": "TYP Yönetmeliği Md. 11/4 gereğince 5 günlük izin süresi aşıldığından İLİŞİK DERHAL KESİLİR!",
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
                "mesaj": "4857 sayılı İş Kanunu Md. 25/II-g uyarınca 1 ayda 3 işgünü mazeretsiz devamsızlık HAKLI NEDENLE DERHAL FESİH sebebidir.",
                "yasal_dayanak": "4857 Sayılı Kanun Madde 25/II-g"
            }
        elif mazeretsiz_gun >= 2:
            return {
                "seviye": "UYARI",
                "mesaj": "4857 sayılı İş Kanunu Md. 25/II-g uyarınca ardı ardına 2 işgünü devamsızlık fesih hakkı doğurur.",
                "yasal_dayanak": "4857 Sayılı Kanun Madde 25/II-g"
            }
    elif g in ["Kadrolu", "Görevlendirme"]:
        if mazeretsiz_gun >= 20:
            return {
                "seviye": "KRİTİK",
                "mesaj": "657 sayılı DMK Md. 125/E-d gereğince bir yılda toplam 20 gün özürsüz göreve gelmeyen personel DEVLET MEMURLUĞUNDAN ÇIKARILIR.",
                "yasal_dayanak": "657 DMK Madde 125/E-d"
            }
        elif mazeretsiz_gun >= 10:
            return {
                "seviye": "KRİTİK",
                "mesaj": "657 sayılı DMK Md. 94 gereğince kesintisiz 10 gün özürsüz göreve gelmeyen personel ÇEKİLMİŞ (müstafi) sayılır.",
                "yasal_dayanak": "657 DMK Madde 94"
            }
        elif mazeretsiz_gun >= 3:
            return {
                "seviye": "UYARI",
                "mesaj": "657 sayılı DMK Md. 125/D-b gereğince özürsüz kesintisiz 3-9 gün devamsızlık Kademe İlerlemesinin Durdurulması cezasını gerektirir.",
                "yasal_dayanak": "657 DMK Madde 125/D-b"
            }
        elif mazeretsiz_gun >= 1:
            return {
                "seviye": "BİLGİ",
                "mesaj": "657 sayılı DMK Md. 125/C-b gereğince özürsüz 1-2 gün göreve gelmemek Aylıktan Kesme cezasını gerektirir.",
                "yasal_dayanak": "657 DMK Madde 125/C-b"
            }
    elif g == "Sözleşmeli":
        if mazeretsiz_gun >= 10:
            return {
                "seviye": "KRİTİK",
                "mesaj": "MEB Sözleşmeli Öğretmen Yönetmeliği gereğince bir sözleşme döneminde mazeretsiz 10 işgünü devamsızlıkta SÖZLEŞME FESHEDİLİR.",
                "yasal_dayanak": "657 DMK Md. 4/B ve Yönetmelik"
            }
        elif mazeretsiz_gun >= 3:
            return {
                "seviye": "KRİTİK",
                "mesaj": "Sözleşmeli personelde kesintisiz 3 iş günü mazeretsiz devamsızlık SÖZLEŞME FESHİ sebebidir.",
                "yasal_dayanak": "Sözleşmeli Personel Çalıştırılmasına İlişkin Esaslar"
            }
    return None


def ogrenci_devamsizlik_durumu(ozursuz: float, toplam: float, ozel_durum: Optional[str] = None) -> Dict[str, Any]:
    """
    MEB Ortaöğretim Kurumları Yönetmeliği Madde 36'ya göre öğrencinin yasal risk durumunu hesaplar.
    """
    kurallar = OGRENCI_MEVZUAT_KURALLARI
    genel_ozursuz_sinir = kurallar["genel_devamsizlik_sinirlari"]["ozursuz_azami"]
    genel_toplam_sinir = kurallar["genel_devamsizlik_sinirlari"]["toplam_azami"]

    aktif_ozursuz_sinir = genel_ozursuz_sinir
    aktif_toplam_sinir = genel_toplam_sinir
    ozel_ad = "Standart Öğrenci"

    if ozel_durum and ozel_durum in kurallar["ozel_durum_sinirlari"]:
        ozel_kayit = kurallar["ozel_durum_sinirlari"][ozel_durum]
        aktif_ozursuz_sinir = ozel_kayit["ozursuz_azami"]
        aktif_toplam_sinir = ozel_kayit["toplam_azami"]
        ozel_ad = ozel_kayit["ad"]

    kaldi_mi = (ozursuz > aktif_ozursuz_sinir) or (toplam > aktif_toplam_sinir)
    tebligat_gerekli = False
    tebligat_asamasi = None

    if ozursuz >= 25 or toplam >= 25:
        tebligat_gerekli = True
        tebligat_asamasi = "3. Nihai Tebligat (25. Gün Eşiği)"
    elif ozursuz >= 15 or toplam >= 15:
        tebligat_gerekli = True
        tebligat_asamasi = "2. Resmi Tebligat (15. Gün Eşiği)"
    elif ozursuz >= 5 or toplam >= 5:
        tebligat_gerekli = True
        tebligat_asamasi = "1. Uyarı Tebligatı ve Komisyon Daveti (5. Gün Eşiği)"

    return {
        "ozursuz": ozursuz,
        "toplam": toplam,
        "ozel_durum": ozel_ad,
        "ozursuz_sinir": aktif_ozursuz_sinir,
        "toplam_sinir": aktif_toplam_sinir,
        "sinif_tekrar_riski": kaldi_mi,
        "tebligat_gerekli": tebligat_gerekli,
        "tebligat_asamasi": tebligat_asamasi,
        "sosyal_sorumluluk_saati": int(ozursuz)
    }


def ogrenci_tebligat_ve_artarda_analiz(
    ogrenci_devleri: List[Dict[str, Any]], 
    ozursuz: float, 
    ozurlu: float
) -> Dict[str, Any]:
    """
    MEB Ortaöğretim Kurumları Yönetmeliği Madde 36 gereğince:
    - 5., 15. ve 25. gün resmi tebligat eşiklerini,
    - Art arda 2 gün özürsüz devamsızlık durumunu (Hafta sonu Cuma-Pazartesi geçişleri dahil)
    tespit eder ve bildirim nesnesi döner.
    """
    toplam = round(ozursuz + ozurlu, 1)

    # 1. Tebligat Eşiği Tespiti (Madde 36/4: 5., 15. ve 25. günlerde tebligat)
    tebligat_asamasi = None
    tebligat_etiketi = None
    tebligat_aciklama = ""

    if toplam >= 25.0 or ozursuz >= 25.0:
        tebligat_asamasi = "25_gun"
        tebligat_etiketi = "3. Nihai Tebligat (25. Gün Eşiği)"
        tebligat_aciklama = f"Toplam {toplam} gün devamsızlık (Özürsüz: {ozursuz}G). 30 gün yasal sınır öncesi son resmi tebligat."
    elif toplam >= 15.0 or ozursuz >= 15.0:
        tebligat_asamasi = "15_gun"
        tebligat_etiketi = "2. Resmi Tebligat (15. Gün Eşiği)"
        tebligat_aciklama = f"Toplam {toplam} gün devamsızlık (Özürsüz: {ozursuz}G). 2. bildirim eşiği aşılmıştır."
    elif ozursuz >= 5.0 or (4.5 <= ozursuz <= 5.5):
        tebligat_asamasi = "5_gun"
        tebligat_etiketi = "1. Resmi Tebligat (5. Gün Eşiği)"
        tebligat_aciklama = f"Özürsüz {ozursuz} gün devamsızlık. Veli okula davet edilmeli ve Önleme Komisyonunca görüşülmelidir (Md. 36/5-a)."

    # 2. Art Arda 2 Gün Özürsüz Devamsızlık Tespiti (Madde 36/4: Veliye derhal bildirim & okula davet)
    ozursuz_tarihler = set()
    for d in ogrenci_devleri:
        tur = str(d.get("tur", "")).strip().upper()
        if tur in ["D", "ÖY", "SY", "OZURSUZ", "ÖZÜRSÜZ"]:
            try:
                t_str = str(d.get("tarih", "")).strip().replace(".", "/").replace("-", "/")
                parts = t_str.split("/")
                if len(parts) == 3:
                    if len(parts[0]) == 4:
                        dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    else:
                        dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                    ozursuz_tarihler.add(dt)
            except Exception:
                pass

    sirali_tarihler = sorted(list(ozursuz_tarihler))
    art_arda = False
    art_arda_ciftler = []

    for i in range(len(sirali_tarihler) - 1):
        d1 = sirali_tarihler[i]
        d2 = sirali_tarihler[i + 1]
        delta = (d2 - d1).days

        # Takvimde ardışık gün (Pazartesi-Salı vb.)
        if delta == 1:
            art_arda = True
            art_arda_ciftler.append(f"{d1.strftime('%d/%m/%Y')} - {d2.strftime('%d/%m/%Y')}")
        # Cuma'dan Pazartesi'ye hafta sonu atlayarak ardışık okul günü (delta=3, Cuma=4, Pazartesi=0)
        elif delta == 3 and d1.weekday() == 4 and d2.weekday() == 0:
            art_arda = True
            art_arda_ciftler.append(f"{d1.strftime('%d/%m/%Y')} - {d2.strftime('%d/%m/%Y')} (Hafta Sonu Geçişli)")

    son_art_arda_tarih = art_arda_ciftler[-1] if art_arda_ciftler else ""
    art_arda_aciklama = ""
    if art_arda:
        art_arda_aciklama = (
            f"Öğrenci {son_art_arda_tarih} tarihlerinde art arda 2 gün özürsüz devamsızlık yapmıştır. "
            f"MEB Ortaöğretim Kurumları Yönetmeliği Md. 36/4 gereğince veli derhal bilgilendirilmeli, "
            f"okula davet edilerek varsa mazeret belgesi istenmelidir."
        )

    return {
        "tebligat_gerekli": tebligat_asamasi is not None,
        "tebligat_asamasi": tebligat_asamasi,
        "tebligat_etiketi": tebligat_etiketi,
        "tebligat_aciklama": tebligat_aciklama,
        "art_arda_2gun": art_arda,
        "art_arda_tarihler": son_art_arda_tarih,
        "art_arda_ciftler": art_arda_ciftler,
        "art_arda_aciklama": art_arda_aciklama,
        "acil_bildirim_var_mi": art_arda or (tebligat_asamasi is not None)
    }


def kariyer_basamagi_hakki(hizmet_yili: int, mevcut_unvan: str = "Öğretmen", ceza_var_mi: bool = False) -> Dict[str, Any]:
    """
    7528 sayılı Öğretmenlik Mesleği Kanununa göre personelin kazanabileceği kariyer basamağını değerlendirir.
    """
    if ceza_var_mi:
        return {
            "basvuru_yapabilir_mi": False,
            "hak_kazanilan_unvan": mevcut_unvan,
            "gerekce": "Kademe ilerlemesinin durdurulması cezası bulunanlar ceza özlükten silinmeden başvuramaz (Md. 11/1-c)."
        }

    mevcut_unvan_temiz = (mevcut_unvan or "").strip()
    if "Başöğretmen" in mevcut_unvan_temiz:
        return {
            "basvuru_yapabilir_mi": False,
            "hak_kazanilan_unvan": "Başöğretmen",
            "gerekce": "Zaten en üst kariyer basamağındadır."
        }

    # 18/10/2024 Geçici Madde 1: Öğretmenlikte 20 yıl hizmeti olanlar doğrudan Başöğretmenliğe başvurabilir
    if hizmet_yili >= 20:
        return {
            "basvuru_yapabilir_mi": True,
            "hak_kazanilan_unvan": "Başöğretmen",
            "derece_artisi": "+1 Derece",
            "gerekce": "7528 SK Geçici Md. 1 gereğince 20 yıllık hizmet ile doğrudan Başöğretmenlik başvuru hakkı mevcuttur."
        }
    elif "Uzman" in mevcut_unvan_temiz and hizmet_yili >= 10:
        return {
            "basvuru_yapabilir_mi": True,
            "hak_kazanilan_unvan": "Başöğretmen",
            "derece_artisi": "+1 Derece",
            "gerekce": "Uzman öğretmenlikte 10 yıl hizmet ve eğitim şartı tamamlanarak Başöğretmenlik unvanı kazanılır."
        }
    elif hizmet_yili >= 10:
        return {
            "basvuru_yapabilir_mi": True,
            "hak_kazanilan_unvan": "Uzman Öğretmen",
            "derece_artisi": "+1 Derece",
            "gerekce": "7528 SK Md. 11 gereğince 10 yıllık öğretmenlik hizmeti ile Uzman Öğretmenlik unvanı kazanılır."
        }

    kalan = 10 - hizmet_yili
    return {
        "basvuru_yapabilir_mi": False,
        "hak_kazanilan_unvan": mevcut_unvan_temiz or "Öğretmen",
        "gerekce": f"Uzman Öğretmenlik için en az {kalan} yıl daha hizmet süresi gereklidir."
    }


# ==============================================================================
# PERSONEL GÖREV VE UZUN SÜRELİ İZİN DURUMLARI REHBERİ
# ==============================================================================
PERSONEL_DURUMLARI_REHBERI: Dict[int, Dict[str, Any]] = {
    1: {
        "kod": 1,
        "ad": "Aktif (Görevde)",
        "kisa_ad": "Aktif",
        "renk": "#059669",
        "bg_renk": "rgba(16, 185, 129, 0.12)",
        "border_renk": "rgba(16, 185, 129, 0.35)",
        "ikon": "check-circle-2",
        "fiilen_gorevde": True,
        "yasal_dayanak": "Fiilen Görevde",
        "aciklama": "Kurumda fiilen görev başındadır. İmza sirküsü ve resmi listelerde varsayılan olarak seçili gelir."
    },
    0: {
        "kod": 0,
        "ad": "Başka Kuruma Görevlendirildi",
        "kisa_ad": "Başka Kurumda",
        "renk": "#dc2626",
        "bg_renk": "rgba(239, 68, 68, 0.12)",
        "border_renk": "rgba(239, 68, 68, 0.35)",
        "ikon": "building-2",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Ek Md. 8 / MEB Yönetici Görevlendirme",
        "aciklama": "Başka bir kuruma geçici görevlendirildiği için kurumdaki günlük tebliğ listelerine dahil edilmez."
    },
    2: {
        "kod": 2,
        "ad": "Uzun Süreli Sağlık İzninde",
        "kisa_ad": "Sağlık İzninde",
        "renk": "#7c3aed",
        "bg_renk": "rgba(124, 58, 237, 0.12)",
        "border_renk": "rgba(124, 58, 237, 0.35)",
        "ikon": "heart-pulse",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 105",
        "aciklama": "Kanser, verem, akıl hastalığı gibi durumlarda 18 aya, diğer hastalıklarda 12 aya kadar sağlık kurulu raporlu sıhhi izinlidir."
    },
    3: {
        "kod": 3,
        "ad": "Doğum / Analık İzninde",
        "kisa_ad": "Doğum İzninde",
        "renk": "#db2777",
        "bg_renk": "rgba(236, 72, 153, 0.12)",
        "border_renk": "rgba(236, 72, 153, 0.35)",
        "ikon": "baby",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 104/A",
        "aciklama": "Doğum öncesi ve sonrası 8'er hafta (çoğulda doğum öncesi 10 hafta) olmak üzere 16-18 hafta analık izinlidir."
    },
    4: {
        "kod": 4,
        "ad": "Aylıksız İzninde",
        "kisa_ad": "Aylıksız İzninde",
        "renk": "#d97706",
        "bg_renk": "rgba(217, 119, 6, 0.12)",
        "border_renk": "rgba(217, 119, 6, 0.35)",
        "ikon": "clock",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 108",
        "aciklama": "Doğum sonrası 24 aya kadar veya 5 hizmet yılını dolduran memura isteğiyle 1 yıla kadar verilen aylıksız izinlidir."
    },
    5: {
        "kod": 5,
        "ad": "Refakat İzninde",
        "kisa_ad": "Refakat İzninde",
        "renk": "#0891b2",
        "bg_renk": "rgba(8, 145, 178, 0.12)",
        "border_renk": "rgba(8, 145, 178, 0.35)",
        "ikon": "shield-alert",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 105/Son",
        "aciklama": "Ağır kaza veya hayati tehlike geçiren birinci derece yakını için sağlık kurulu raporuyla 3 aya kadar (+3 ay uzatmalı) refakat izinlidir."
    },
    6: {
        "kod": 6,
        "ad": "Askerlik Görevinde / İzninde",
        "kisa_ad": "Askerlikte",
        "renk": "#4d7c0f",
        "bg_renk": "rgba(77, 124, 15, 0.12)",
        "border_renk": "rgba(77, 124, 15, 0.35)",
        "ikon": "shield",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 108/G",
        "aciklama": "Muvazzaf veya bedelli askerlik hizmetini ifa etmek üzere aylıksız izinlidir."
    },
    7: {
        "kod": 7,
        "ad": "Yurtdışı / Lisansüstü Eğitim İzninde",
        "kisa_ad": "Yurtdışı/Eğitim",
        "renk": "#4f46e5",
        "bg_renk": "rgba(79, 70, 229, 0.12)",
        "border_renk": "rgba(79, 70, 229, 0.35)",
        "ikon": "globe",
        "fiilen_gorevde": False,
        "yasal_dayanak": "657 SK Md. 78-79",
        "aciklama": "Lisansüstü eğitim, yabancı dil veya bilgi-görgü artırma amacıyla yurt dışı veya eğitim izinlidir."
    },
    8: {
        "kod": 8,
        "ad": "Sendika Görevinde / İzninde",
        "kisa_ad": "Sendika İzninde",
        "renk": "#c026d3",
        "bg_renk": "rgba(192, 38, 211, 0.12)",
        "border_renk": "rgba(192, 38, 211, 0.35)",
        "ikon": "landmark",
        "fiilen_gorevde": False,
        "yasal_dayanak": "4688 SK Md. 18",
        "aciklama": "Sendika veya konfederasyon yönetim kurullarında profesyonel sendikacılık amacıyla izinlidir."
    }
}


def tum_mevzuat_ozeti() -> Dict[str, Any]:
    """
    Sistemdeki tüm güncel mevzuat kurallarını, dayanak belgeleri ve yasal sınırları tek bir sözlükte sunar.
    """
    return {
        "dayanak_envanteri": DAYANAK_MEVZUAT_ENVANTERI,
        "personel_statu_matrisi": MEVZUAT_MATRISI,
        "personel_durumlari": PERSONEL_DURUMLARI_REHBERI,
        "ogrenci_devamsizlik_mevzuati": OGRENCI_MEVZUAT_KURALLARI,
        "kariyer_basamaklari": KARIYER_BASAMAKLARI_KURALLARI,
        "yonetici_hiyerarsisi": YONETICI_GOREVLERI_KURALLARI
    }
