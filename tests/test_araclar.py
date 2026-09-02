import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from araclar import VeriAraclari

def test_haftasonu_haric_hesaplama():
    """Hafta sonuna denk gelen devamsızlıkların genel toplamdan düşülüp düşülmediğini test eder."""
    
    ornek_devamsizliklar = [
        # 1. Kayıt: 1 Tam gün hafta içi (Cuma) - Özürsüz (D)
        {'no': '852', 'tarih': '01/05/2026', 'tur': 'D', 'gun': '1'}, 
        
        # 2. Kayıt: 2 Tam gün (Cumartesi ve Pazar) - Özürlü (İ)
        # Normalde 2 gün ekler ama hafta sonu olduğu için NET TOPLAMA 0 geçmeli!
        {'no': '852', 'tarih': '02/05/2026', 'tur': 'İ', 'gun': '2'}, 
        
        # 3. Kayıt: 1.5 Gün (Pazartesi ve Salı yarım) - Özürsüz (D)
        {'no': '852', 'tarih': '04/05/2026', 'tur': 'D', 'gun': '1.5'}, 
    ]

    ozsz_net, ozrl_net = VeriAraclari.hesapla_devamsizlik('852', ornek_devamsizliklar, [])

    # Özürsüz (D) = 1 (Cuma) + 1.5 (Pzt-Salı) = 2.5 Gün
    # Özürlü (İ)  = Sadece Cmt-Pzr'ye denk geldiği için = 0.0 Gün
    assert ozsz_net == 2.5, f"HATA! Özürsüz hesaplaması bozuk. Beklenen: 2.5, Sistemdeki: {ozsz_net}"
    assert ozrl_net == 0.0, f"HATA! Hafta sonu filtresi bozulmuş. Beklenen: 0.0, Sistemdeki: {ozrl_net}"

def test_gec_kalma_hesaplamasi():
    """5 adet Geç (G) kalmanın tam olarak 0.5 gün Özürsüz yapıp yapmadığını test eder."""
    
    ornek_dev = [
        {'no': '852', 'tarih': '01/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '02/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '03/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '04/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '05/05/2026', 'tur': 'G', 'gun': '1'},
    ]
    
    ozsz_net, ozrl_net = VeriAraclari.hesapla_devamsizlik('852', ornek_dev, [])
    assert ozsz_net == 0.5, "HATA! 5 adet Geç (G) kaydı 0.5 gün Özürsüz yapmalıdır!"
