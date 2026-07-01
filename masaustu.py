import webview
import threading
import uvicorn
import os
import time

# api.py içindeki FastAPI motorumuzu (app) buraya çağırıyoruz
from api import app 

def sunucuyu_baslat():
    # Arka planda gizlice API sunucusunu çalıştırır
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="critical")

if __name__ == '__main__':
    # 1. Aşçıyı (Python Sunucusunu) arka planda işe başlat
    t = threading.Thread(target=sunucuyu_baslat)
    t.daemon = True
    t.start()
    
    # Sunucunun ayaklanması için çok kısa bir süre bekle
    time.sleep(1)

    # 2. Tasarladığımız HTML dosyasının yolunu bul
    html_yolu = os.path.join(os.getcwd(), 'index.html')

    # 3. Modern masaüstü penceresini oluştur ve HTML'i içine göm!
    pencere = webview.create_window(
        title='Oto-Yoklama Sistemi V2', 
        url=html_yolu,
        width=1000, 
        height=700,
        resizable=True,
        background_color='#0F172A' # Yüklenirken siyah ekran vermesi için tema rengimiz
    )
    
    # 4. Programı başlat
    webview.start()