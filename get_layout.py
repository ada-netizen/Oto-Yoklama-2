from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
for page_layout in extract_pages('Muayene ve Kabul Belgesi.pdf'):
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            print(repr(element.get_text().strip()) + ' -> x=' + str(round(element.bbox[0])) + ', y=' + str(round(element.bbox[1])))
