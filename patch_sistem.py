with open('routes/sistem.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_route = '''
@router.post("/arsivle")
async def arsivle_sistem(request: Request):
    data = await request.json()
    arsiv_adi = data.get("arsiv_adi", "Arsiv")
    
    import shutil, os
    from dependencies import db, yollar
    
    arsiv_klasoru = os.path.join(yollar["ANA"], "Arsivler", arsiv_adi)
    os.makedirs(arsiv_klasoru, exist_ok=True)
    
    try:
        # Copy DB
        if os.path.exists(yollar["DB"]):
            shutil.copy(yollar["DB"], os.path.join(arsiv_klasoru, "yoklama_veritabani.db"))
        
        # Copy PDFs
        if os.path.exists(yollar["PDF"]):
            hedef_pdf = os.path.join(arsiv_klasoru, "PDF_Ciktilari")
            if os.path.exists(hedef_pdf):
                shutil.rmtree(hedef_pdf)
            shutil.copytree(yollar["PDF"], hedef_pdf)
            
        # Sifirla DB (Keep personel)
        db.sifirla()
        
        return {"basarili": True, "mesaj": "Arşivleme tamamlandı ve veritabanı sıfırlandı."}
    except Exception as e:
        return {"basarili": False, "mesaj": f"Hata: {str(e)}"}
'''

with open('routes/sistem.py', 'w', encoding='utf-8') as f:
    f.write(content + new_route)
