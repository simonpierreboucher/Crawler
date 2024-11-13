from src.constants import *
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import io

class ContentExtractor:
    """Classe gérant l'extraction de contenu"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content):
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text() or '')
            return '\n'.join(text)
        except Exception as e:
            logging.error(f"Erreur extraction PDF: {str(e)}")
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
