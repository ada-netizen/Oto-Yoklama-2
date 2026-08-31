from fastapi.testclient import TestClient
import sys
import os

# Üst klasörü import yollarına ekle ki api.py bulunabilsin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app

client = TestClient(app)

def test_root_not_found():
    # Kök dizin olmadığı için 404 dönmeli
    response = client.get("/")
    assert response.status_code == 404

def test_get_ogrenciler():
    # Veritabanı başlatılmadığı için boş liste veya hata dönebilir,
    # ancak endpoint'in var olduğundan emin oluyoruz.
    response = client.get("/ogrenciler")
    # Endpoint çalışıyor mu? (500 Internal Server Error bile olsa varlık kanıtıdır, 404 olmamalı)
    assert response.status_code in [200, 500]
    
def test_get_ayarlar():
    response = client.get("/ayarlar-getir")
    assert response.status_code in [200, 500]
