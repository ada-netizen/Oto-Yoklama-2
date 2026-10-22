@echo off
chcp 65001 > nul
title Okul Yonetim Sistemi - Yonetici Sifre Sifirlama Araci
echo.
echo =======================================================
echo   SISTEM YONETICISI SIFRE SIFIRLAMA ARACI BASLATILIYOR...
echo =======================================================
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe sifre_sifirla.py
) else (
    python sifre_sifirla.py
)

pause

