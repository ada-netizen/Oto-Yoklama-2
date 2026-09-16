import re

p = 'frontend/js/core.js'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('ogrenciSec(ogr.no, ogr.ad_soyad, ogr.ozsz, ogr.ozrl)', 'ogrenciSec(ogr.no, ogr.ad_soyad, ogr.temizSube, ogr.ozsz, ogr.ozrl)')
c = c.replace('function ogrenciSec(no, ad, ozsz, ozrl) {', 'function ogrenciSec(no, ad, sube, ozsz, ozrl) {')
c = c.replace('seciliOgrenci = { no: no, ad: ad, ozsz: parseFloat(ozsz || 0), ozrl: parseFloat(ozrl || 0) };', 'seciliOgrenci = { no: no, ad: ad, sube: sube, ozsz: parseFloat(ozsz || 0), ozrl: parseFloat(ozrl || 0) };')
c = c.replace("const sube = document.querySelector('.tr-secili td')?.innerText || \"Bilinmiyor\";", "const sube = seciliOgrenci.sube || \"Bilinmiyor\";")

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print("done")
