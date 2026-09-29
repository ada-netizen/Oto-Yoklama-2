with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

old_section = (
    "### Normal Kullanıcılar İçin (Önerilen)\n"
    "Artık terminal ile uğraşmanıza gerek yok! \n"
    "1. Projenin `dist` klasörü içindeki `Oto_Yoklama.exe` dosyasını çalıştırın.\n"
    "2. Program otomatik olarak arka planda kendi sunucusunu başlatacak ve modern masaüstü uygulamasını karşınıza getirecektir. (USB belleğe atıp istediğiniz bilgisayarda kullanabilirsiniz)."
)

new_section = (
    "### Normal Kullanıcılar İçin (Önerilen)\n"
    "Artık terminal ile uğraşmanıza gerek yok!\n"
    "1. GitHub Releases sayfasından en güncel `Elektronik_Okul_Vx.x_Setup.exe` kurulum dosyasını indirin.\n"
    "2. Kurulum dosyasını çalıştırın.\n"
    "3. Program otomatik olarak arka planda kendi sunucusunu başlatacak ve modern masaüstü uygulamasını karşınıza getirecektir.\n"
    "\n"
    "> [!NOTE]\n"
    "> **Windows Guvenlik Uyarisi Hakkinda**\n"
    ">\n"
    "> Kurulum sirasinda Windows SmartScreen mavi bir uyari ekrani gosterebilir:\n"
    "> *\"Windows bilgisayarinizi korudu — Tanimadigim uygulama...\"*\n"
    ">\n"
    "> Bu uyari, kurulum dosyasinin henuz dijital imzasi (Code Signing Certificate) bulunmadigi icin cikmaktadir. Program tamamen guvenlidir.\n"
    ">\n"
    "> **Cozum:**\n"
    "> 1. **\"Daha fazla bilgi\"** linkine tiklayin\n"
    "> 2. Ardindan **\"Yine de calistir\"** butonuna basin\n"
    "> 3. Kurulum normal sekilde devam edecektir"
)

if old_section in content:
    content = content.replace(old_section, new_section)
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('README updated OK')
else:
    print('Section not found exactly, writing to end of file instead')
    with open('README.md', 'a', encoding='utf-8') as f:
        f.write('\n\n' + new_section)
    print('Appended OK')
