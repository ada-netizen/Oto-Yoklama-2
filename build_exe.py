import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'masaustu.py',
    '--name=Oto_Yoklama',
    '--windowed',
    '--onefile',
    '--icon=logo.ico',
    '--add-data=index.html;.',
    '--add-data=app.js;.',
    '--add-data=style.css;.',
    '--add-data=lucide.min.js;.',
    '--add-data=versiyon.txt;.',
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    '--hidden-import=uvicorn.lifespan',
    '--hidden-import=uvicorn.lifespan.on',
    '--hidden-import=uvicorn.lifespan.off',
    '--hidden-import=webview',
    '--clean'
])
