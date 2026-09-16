document.addEventListener('alpine:init', () => {
    Alpine.store('appStore', {
        ogrenciler: [],
        personeller: [],
        aktifSube: '',
        karanlikMod: localStorage.getItem('temaPref') === 'gece' || false,
        yukleniyor: false,
        
        async initData() {
            this.yukleniyor = true;
            try {
                // Burada fetch ile ogrenciler ve personeller cekilecek
                // const res = await fetch('/ogrenciler');
                // const veriler = await res.json();
                // this.ogrenciler = veriler.ogrenciler || [];
            } catch (error) {
                console.error("Veri yukleme hatasi", error);
            } finally {
                this.yukleniyor = false;
            }
        },

        toggleTema() {
            this.karanlikMod = !this.karanlikMod;
            localStorage.setItem('temaPref', this.karanlikMod ? 'gece' : 'gunduz');
            document.documentElement.setAttribute('data-theme', this.karanlikMod ? 'dark' : 'light');
        }
    });
});
