# src/pdf_processor.py
from PyPDF2 import PdfReader
import pdfplumber
import pytesseract
from PIL import Image
import io
import logging

class PDFProcessor:
    """Gère l'extraction avancée de texte à partir de PDFs"""
    
    def __init__(self):
        self.tesseract_config = r'--oem 3 --psm 6'
        self.languages = ['fra']  # Ajoutez d'autres langues si nécessaire, par exemple ['fra', 'eng']
    
    def extract_text_from_pdf(self, pdf_content):
        """Extrait le texte d'un PDF en utilisant pdfplumber et OCR si nécessaire"""
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
                text = self.extract_text_via_ocr(pdf_content)
            
            return text
        except Exception as e:
            logging.error(f"Erreur extraction PDF: {str(e)}")
            return ""
    
    def extract_text_via_ocr(self, pdf_content):
        """Extrait le texte d'un PDF en utilisant OCR (Tesseract)"""
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    if not page.extract_text():
                        logging.info(f"Extraction OCR pour la page {page_number}")
                        # Extraire l'image complète de la page
                        pil_image = page.to_image(resolution=300).original
                        
                        # Utiliser pytesseract pour extraire le texte de l'image
                        ocr_text = pytesseract.image_to_string(
                            pil_image,
                            config=self.tesseract_config,
                            lang='+'.join(self.languages)
                        )
                        text += ocr_text + "\n"
            return text
        except Exception as e:
            logging.error(f"Erreur extraction OCR PDF: {str(e)}")
            return ""
