
document.addEventListener("alpine:init", () => {
    Alpine.data("ogrenciYonetimComponent", () => ({
        arama: "",
        aktifFiltre: "Tümü",
        formAcik: false,
        duzenlenenOgrenci: { no: "", ad_soyad: "", sube: "", eski_no: "" },
        ogrenciler: window.ogrenciListesi || [],

        init() {
            window.addEventListener("ogrenciler-guncellendi", () => {
                this.ogrenciler = window.ogrenciListesi || [];
            });
        },
        
        get subeler() {
            let sList = [...new Set(this.ogrenciler.map(o => String(o.sube).trim()))];
            return sList.sort((a, b) => {
                let pa = parseInt(a); let pb = parseInt(b);
                if (!isNaN(pa) && !isNaN(pb)) return pa - pb;
                return a.localeCompare(b);
            });
        },
        
        get gosterilecekOgrenciler() {
            let filterText = this.arama.toLocaleUpperCase("tr-TR");
            let arr = [...this.ogrenciler].sort((a,b) => {
                let p1 = parseInt(a.sube)||99, p2 = parseInt(b.sube)||99;
                if(p1 !== p2) return p1 - p2;
                return a.ad_soyad.localeCompare(b.ad_soyad);
            });
            
            return arr.filter(o => {
                if(filterText && !o.ad_soyad.toLocaleUpperCase("tr-TR").includes(filterText) && !String(o.no).includes(filterText)) return false;
                if(this.aktifFiltre !== "Tümü" && String(o.sube).trim() !== this.aktifFiltre) return false;
                return true;
            });
        },
        
        yeniEkle() {
            this.duzenlenenOgrenci = { no: "", ad_soyad: "", sube: "", eski_no: "" };
            this.formAcik = true;
        },
        
        duzenle(ogr) {
            this.duzenlenenOgrenci = { no: ogr.no, ad_soyad: ogr.ad_soyad, sube: ogr.sube, eski_no: ogr.no };
            this.formAcik = true;
        },
        
        kaydet() {
            if(!this.duzenlenenOgrenci.no || !this.duzenlenenOgrenci.ad_soyad || !this.duzenlenenOgrenci.sube) {
                if(window.bildirimGoster) window.bildirimGoster("Lütfen tüm alanları doldurun.", "hata");
                return;
            }
            fetch(`${window.API || ''}/ogrenci-ekle-guncelle`, { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.duzenlenenOgrenci)
            })
            .then(r => r.json())
            .then(v => {
                if(window.bildirimGoster) window.bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                if (v.basarili) {
                    this.formAcik = false;
                    if(window.verileriYukle) window.verileriYukle();
                }
            })
            .catch(e => {
                if(window.bildirimGoster) window.bildirimGoster("Hata olustu: " + e, "hata");
            });
        },
        
        sil(no, ad) {
            if (!confirm(`${no} numaralı ${ad} adlı öğrenciyi (ve tüm devamsızlıklarını) silmek istediğinize emin misiniz?`)) return;
            fetch(`${window.API || ''}/ogrenci-sil/${encodeURIComponent(no)}`, { method: "DELETE" })
            .then(r => r.json())
            .then(v => {
                if(window.bildirimGoster) window.bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                if (v.basarili) {
                    if(window.verileriYukle) window.verileriYukle();
                }
            })
            .catch(e => {
                if(window.bildirimGoster) window.bildirimGoster("Hata olustu: " + e, "hata");
            });
        }
    }));
});
