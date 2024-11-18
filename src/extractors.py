# src/extractors.py
from src.constants import *
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

class ContentExtractor:
    """Classe gérant l'extraction de contenu"""
    
    @staticmethod
    def extract_text_from_html(html_content):
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
                element.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)
        except Exception as e:
            logging.error(f"Erreur extraction HTML: {str(e)}")
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
