with open('frontend/components/yenilikler_modal.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_footer = '''    <!-- FOOTER -->
    <div style="padding: 15px 20px; background-color: var(--bg-card); border-top: 1px solid var(--border); text-align: center;">
        <button class="btn btn-ogr" @click="acik = false" style="padding: 10px 30px; font-weight: bold; border-radius: 20px; font-size: 14px;">Anladım, Kapat</button>
    </div>'''

new_footer = '''    <!-- FOOTER -->
    <div style="padding: 15px 20px; background-color: var(--bg-card); border-top: 1px solid var(--border);">
        <div style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.3); border-radius: 8px; padding: 12px 15px; margin-bottom: 12px; display: flex; gap: 10px; align-items: flex-start;">
            <i data-lucide="shield-alert" height="18" width="18" style="color:#F59E0B; flex-shrink:0; margin-top:2px;"></i>
            <div style="font-size:12px; color: var(--fg-sub); line-height:1.5;">
                <strong style="color:var(--fg-main);">Kurulum sirasinda Windows uyarisi alirsiniz:</strong><br>
                "Daha fazla bilgi" linkine tiklayin, ardindan <strong>"Yine de calistir"</strong> butonuna basin.
                Program tamamen guvenlidir; bu uyari dijital imza eksikliginden kaynaklanmaktadir.
            </div>
        </div>
        <div style="text-align:center;">
            <button class="btn btn-ogr" @click="acik = false" style="padding: 10px 30px; font-weight: bold; border-radius: 20px; font-size: 14px;">Anladim, Kapat</button>
        </div>
    </div>'''

if old_footer in content:
    content = content.replace(old_footer, new_footer)
    with open('frontend/components/yenilikler_modal.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('yenilikler_modal updated OK')
else:
    print('Footer not found')
    # try finding partial match
    if 'FOOTER' in content:
        idx = content.index('FOOTER')
        print(repr(content[idx-5:idx+300]))
