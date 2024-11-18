from src.constants import *
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import io
import pdfplumber
import pytesseract
from PIL import Image
import tempfile

class ContentExtractor:
    """Classe gérant l'extraction de contenu"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content):
        text = ""
        try:
            # Première tentative avec pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if not text.strip():
                # Si pdfplumber ne trouve pas de texte, utiliser OCR avec pytesseract
                logging.info("pdfplumber n'a pas pu extraire de texte, tentative avec OCR")
                text = ContentExtractor.extract_text_via_ocr(pdf_content)
            
            return text
        except Exception as e:
            logging.error(f"Erreur extraction PDF: {str(e)}")
            return ""

    @staticmethod
    def extract_text_via_ocr(pdf_content):
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    if not page.extract_text():
                        logging.info(f"Extraction OCR pour la page {page_number}")
                        # Extraire l'image complète de la page
                        pil_image = page.to_image(resolution=300).original
                        
                        # Utiliser pytesseract pour extraire le texte de l'image
                        ocr_text = pytesseract.image_to_string(pil_image, lang='fra')  # Modifier la langue si nécessaire
                        text += ocr_text + "\n"
            return text
        except Exception as e:
            logging.error(f"Erreur extraction OCR PDF: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_html(html_content):
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
                element.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)
        except Exception as e:
            logging.error(f"Erreur extraction HTML: {str(e)}")
            return ""

    @staticmethod
    def extract_text_alternative(html_content):
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            logging.error(f"Erreur extraction HTML alternative: {str(e)}")
            return ""

    @staticmethod
    def extract_links(html_content, base_url):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href:
                    # Normalise les URLs relatives
                    if not href.startswith(('http://', 'https://')):
                        if href.startswith('//'):
                            href = f"https:{href}"
                        elif href.startswith('/'):
                            href = f"https://{urlparse(base_url).netloc}{href}"
                        else:
                            href = f"https://{urlparse(base_url).netloc}/{href}"
                    links.append(href)
            return links
        except Exception as e:
            logging.error(f"Erreur extraction liens: {str(e)}")
            return []
