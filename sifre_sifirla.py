#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKUL YÖNETİM SİSTEMİ - FİZİKSEL ANA MAKİNE ŞİFRE SIFIRLAMA & ACİL KURTARMA ARACI
-----------------------------------------------------------------------------
Bu betik yalnızca ana bilgisayarda fiziksel olarak veritabanına erişimi olan
yetkili tarafından doğrudan çalıştırılır. Ağ veya şifre bağımlılığı olmadan
Süper Yönetici veya herhangi bir kullanıcının şifresini anında sıfırlar.
"""

import sys
import sqlite3
import os

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dependencies import db, yollar
from veritabani import sifre_hashle

DB_PATH = yollar.get("DB", "okul_veritabani.db")

def main():
    print("=" * 65)
    print("  ELEKTRONIK OKUL - SUPER YONETICI ACIL SIFRE KURTARMA ARACI")
    print("=" * 65)
    print(f"Hedef Veritabanı: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("\n[HATA] Veritabani dosyasi bulunamadi!")
        input("\nCikmak icin Enter tusuna basiniz...")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Kullanıcılar tablosu var mı kontrol et
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kullanicilar'")
    if not cursor.fetchone():
        print("\n[BILGI] Kullanicilar tablosu henuz olusturulmamis. Lutfen once uygulamayi baslatiniz.")
        conn.close()
        input("\nCikmak icin Enter tusuna basiniz...")
        return

    # Süper yöneticiyi bul
    cursor.execute("SELECT id, ad_soyad, kullanici_adi, unvan FROM kullanicilar WHERE super_admin_mi = 1 LIMIT 1")
    super_admin = cursor.fetchone()

    if not super_admin:
        print("\n[BILGI] Sistemde henuz kayitli bir Super Yonetici bulunmuyor.")
        print("Tum kullanicilar:")
        cursor.execute("SELECT id, ad_soyad, kullanici_adi, rol FROM kullanicilar")
        users = cursor.fetchall()
        if not users:
            print("  (Kayitli hicbir kullanici yok. Web arayuzunden ilk kurulumu tamamlayiniz.)")
            conn.close()
            input("\nCikmak icin Enter tusuna basiniz...")
            return
        for u in users:
            print(f"  [{u['id']}] {u['ad_soyad']} ({u['kullanici_adi']}) - {u['rol']}")
        secim = input("\nSifresini sifirlamak istediginiz Kullanici ID: ").strip()
        cursor.execute("SELECT id, ad_soyad, kullanici_adi, unvan FROM kullanicilar WHERE id = ?", (secim,))
        target_user = cursor.fetchone()
        if not target_user:
            print("[HATA] Gecersiz ID!")
            conn.close()
            input("\nCikmak icin Enter tusuna basiniz...")
            return
    else:
        target_user = super_admin

    print(f"\nSecili Hesap: {target_user['ad_soyad']} ({target_user['kullanici_adi']}) - {target_user['unvan'] or 'Yonetici'}")
    yeni_sifre = input("Yeni Sifreyi Giriniz (Varsayilan: admin123): ").strip()
    if not yeni_sifre:
        yeni_sifre = "admin123"

    yeni_hash, yeni_salt = sifre_hashle(yeni_sifre)

    # Şifreyi güncelle ve kilitleri kaldır
    cursor.execute("""
        UPDATE kullanicilar 
        SET sifre_hash = ?, salt = ?, aktif = 1
        WHERE id = ?
    """, (yeni_hash, yeni_salt, target_user['id']))

    # Denetim kaydı ekle
    try:
        cursor.execute("""
            INSERT INTO islem_denetim_kayitlari (kullanici_id, modul, islem, ayrinti, ip_adresi)
            VALUES (?, 'GÜVENLİK', 'Kurtarma Aracı ile Şifre Sıfırlandı', 'Fiziksel ana makineden sifre_sifirla.py çalıştırıldı', '127.0.0.1')
        """, (target_user['id'],))
    except Exception:
        pass

    conn.commit()
    conn.close()

    print("\n" + "=" * 65)
    print("  [BASARILI] Sifre basariyla guncellendi!")
    print(f"  Kullanici Adi: {target_user['kullanici_adi']}")
    print(f"  Yeni Sifre   : {yeni_sifre}")
    print("=" * 65)
    input("\nCikmak icin Enter tusuna basiniz...")

if __name__ == "__main__":
    main()

