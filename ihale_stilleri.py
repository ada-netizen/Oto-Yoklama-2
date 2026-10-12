"""
ihale_stilleri.py - İhale Belgeleri İçin Ortak Yazı Tipi, Stil ve Excel Biçimlendirme Yöneticisi
ReportLab ve openpyxl için paylaşılan önbellekli stilleri sağlar.
"""
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from openpyxl.styles import Font, Alignment, Border, Side

_FONT_REGISTERED = False
_CACHED_FONT_NAME = 'Helvetica'

def font_hazirla():
    """Türkçe Arial yazı tipini sisteme yalnızca bir kez kaydeder ve adını döndürür."""
    global _FONT_REGISTERED, _CACHED_FONT_NAME
    if _FONT_REGISTERED:
        return _CACHED_FONT_NAME
        
    font_path = r'C:\Windows\Fonts\arial.ttf'
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Arial_TR', font_path))
            _CACHED_FONT_NAME = 'Arial_TR'
            _FONT_REGISTERED = True
            return _CACHED_FONT_NAME
        except Exception:
            pass
    _CACHED_FONT_NAME = 'Helvetica'
    _FONT_REGISTERED = True
    return _CACHED_FONT_NAME

def get_ihale_stilleri(font_name=None, font_size=9, leading=11):
    """Sık kullanılan ParagraphStyle nesnelerini dinamik oluşturur."""
    f_name = font_name or font_hazirla()
    return {
        'normal': ParagraphStyle('Normal_TR', fontName=f_name, fontSize=font_size, leading=leading, wordWrap='CJK'),
        'justify': ParagraphStyle('Justify_TR', fontName=f_name, fontSize=font_size, alignment=4, leading=leading, firstLineIndent=12*mm),
        'center': ParagraphStyle('Center_TR', fontName=f_name, fontSize=font_size, alignment=1, leading=leading, wordWrap='CJK'),
        'right': ParagraphStyle('Right_TR', fontName=f_name, fontSize=font_size, alignment=2, leading=leading, wordWrap='CJK'),
        'title': ParagraphStyle('Title_TR', fontName=f_name, fontSize=font_size + 2, alignment=1, leading=leading + 3, spaceAfter=8, wordWrap='CJK')
    }

# Ortak Excel Biçimleri (openpyxl)
THIN_SIDE = Side(border_style="thin", color="000000")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
DOUBLE_BOTTOM_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=Side(border_style="double", color="000000"))

FONT_TITLE_12 = Font(name='Arial', size=12, bold=True)
FONT_BOLD_9 = Font(name='Arial', size=9, bold=True)
FONT_NORMAL_9 = Font(name='Arial', size=9)
FONT_BOLD_8 = Font(name='Arial', size=8, bold=True)
FONT_NORMAL_8 = Font(name='Arial', size=8)

ALIGN_CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
ALIGN_LEFT = Alignment(horizontal='left', vertical='center')
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center')
ALIGN_JUSTIFY = Alignment(horizontal='justify', vertical='top', wrap_text=True)

