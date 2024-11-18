# src/crawler.py
from src.constants import *
import os
import logging
import sys
import json
from datetime import datetime
from collections import deque
import concurrent.futures
import time
import random
from src.file_handler import FileHandler
from src.pdf_processor import PDFProcessor
from urllib.parse import urlparse
from src.extractors import ContentExtractor
from src.processors import URLProcessor
import requests
import signal
import pyfiglet  # Import pour l'ASCII art

class SafeCrawler:
    """Classe principale du crawler"""
    
    def __init__(self, config, session, content_extractor, url_processor, output_dir, resume=False):
        self.config = config
        self.session = session
        self.content_extractor = content_extractor
        self.url_processor = url_processor
        self.output_dir = output_dir
        self.resume = resume
        
        self.seen_urls = set()
        self.queue = deque()
        self.start_time = time.time()
        
        self.setup_signal_handlers()
        if self.resume:
            self.load_state()
        else:
            self.save_initial_state()
        
        # Initialisation de FileHandler et PDFProcessor
        self.file_handler = FileHandler(self.output_dir)
        logging.info("FileHandler initialisé")
        
        self.pdf_processor = PDFProcessor()
        logging.info("PDFProcessor initialisé")

        self.step_counter = 0  # Compteur de pas pour l'affichage ASCII art
    
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logging.info("Arrêt gracieux du crawler...")
        self.save_state()
        sys.exit(0)

    def save_initial_state(self):
        """Initialise l'état si ce n'est pas une reprise."""
        self.seen_urls = set()
        self.queue = deque()
        self.queue.append(self.config['domain']['start_url'])
        logging.info("État initialisé")

    def save_state(self):
        try:
            state = {
                'seen_urls': list(self.seen_urls),
                'queue': list(self.queue),
                'timestamp': datetime.now().isoformat()
            }
            with open(os.path.join(self.output_dir, 'crawler_state.json'), 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            logging.info("État sauvegardé")
        except Exception as e:
            logging.error(f"Erreur sauvegarde état: {str(e)}")

    def load_state(self):
        try:
            state_path = os.path.join(self.output_dir, 'crawler_state.json')
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.seen_urls = set(state.get('seen_urls', []))
                self.queue.extend(state.get('queue', []))
                logging.info("État chargé")
            else:
                self.save_initial_state()
        except Exception as e:
            logging.error(f"Erreur chargement état: {str(e)}")
            self.save_initial_state()

    def safe_request(self, url, method='GET', **kwargs):
        for attempt in range(self.config['timeouts']['max_retries']):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=(
                        self.config['timeouts']['connect'],
                        self.config['timeouts']['read']
                    ),
                    verify=False,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as http_err:
                if http_err.response and http_err.response.status_code == 404:
                    logging.error(f"Page non trouvée: {url}")
                    break  # Ne pas réessayer pour les erreurs 404
                elif attempt == self.config['timeouts']['max_retries'] - 1:
                    logging.error(f"Max retries atteints pour {url}: {str(http_err)}")
                    raise
                else:
                    logging.warning(f"Retrying {url} ({attempt + 1}/{self.config['timeouts']['max_retries']}) due to error: {str(http_err)}")
                    time.sleep(2 ** attempt)
            except Exception as e:
                if attempt == self.config['timeouts']['max_retries'] - 1:
                    logging.error(f"Max retries atteints pour {url}: {str(e)}")
                    raise
                logging.warning(f"Retrying {url} ({attempt + 1}/{self.config['timeouts']['max_retries']}) due to error: {str(e)}")
                time.sleep(2 ** attempt)

    def process_url(self, url):
        try:
            if not self.url_processor.should_process_url(url):
                return None

            response = self.safe_request(url)
            
            content_type = response.headers.get('Content-Type', '').lower()
            content_main_type = content_type.split(';')[0]  # Pour gérer les paramètres comme charset

            if 'application/pdf' in content_main_type:
                pdf_content = response.content  # Le contenu binaire du PDF
                text = self.pdf_processor.extract_text_from_pdf(pdf_content)
                return ('pdf', url, (text, pdf_content))
            elif 'text/html' in content_main_type:
                text = self.content_extractor.extract_text_from_html(response.content)
                return ('html', url, text)
            elif content_main_type.startswith('image/'):
                return ('image', url, (response.content, content_type))
            elif 'application/msword' in content_main_type or \
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_main_type:
                return ('document', url, response.content)
            else:
                logging.info(f"Type de contenu non supporté pour {url}: {content_type}")
                return None

        except Exception as e:
            logging.error(f"Erreur traitement {url}: {str(e)}")
            return None

    def save_content(self, url, content_type, content):
        """Sauvegarde le contenu extrait avec métadonnées"""
        try:
            filename = self.url_processor.sanitize_filename(url)
            
            if content_type == 'html':
                filepath = os.path.join(self.output_dir, 'text', f"{filename}.txt")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_content = f"""URL: {url}
Timestamp: {timestamp}
Content Type: {content_type}
{'=' * 100}

{content}

{'=' * 100}
Fin du contenu de : {url}"""
                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(formatted_content)
                logging.info(f"Contenu sauvegardé: {url} -> {filepath}")
            elif content_type == 'pdf':
                text, pdf_content = content  # Déballer le tuple
                # Sauvegarder le texte extrait
                txt_filepath = os.path.join(self.output_dir, 'text', f"{filename}.txt")
                os.makedirs(os.path.dirname(txt_filepath), exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_content = f"""URL: {url}
Timestamp: {timestamp}
Content Type: {content_type}
{'=' * 100}

{text}

{'=' * 100}
Fin du contenu de : {url}"""
                with open(txt_filepath, "w", encoding='utf-8') as f:
                    f.write(formatted_content)
                logging.info(f"Texte extrait sauvegardé : {url} -> {txt_filepath}")
                
                # Sauvegarder le PDF original
                pdf_filepath = os.path.join(self.file_handler.files_dir, 'document', f"{filename}.pdf")
                os.makedirs(os.path.dirname(pdf_filepath), exist_ok=True)
                with open(pdf_filepath, "wb") as f:
                    f.write(pdf_content)
                logging.info(f"PDF original sauvegardé : {url} -> {pdf_filepath}")
            elif content_type == 'image':
                image_content, content_type_header = content  # Déballer le tuple
                # Déterminer l'extension à partir du Content-Type
                extension = content_type_header.split('/')[-1]
                filepath = os.path.join(self.file_handler.files_dir, 'image', f"{filename}.{extension}")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(image_content)
                logging.info(f"Image sauvegardée: {url} -> {filepath}")
            elif content_type == 'document':
                # Déterminer l'extension à partir du Content-Type
                if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                    extension = 'docx'
                else:
                    extension = 'doc'
                filepath = os.path.join(self.file_handler.files_dir, 'document', f"{filename}.{extension}")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(content)
                logging.info(f"Document sauvegardé: {url} -> {filepath}")
            else:
                filepath = os.path.join(self.output_dir, 'text', f"{filename}.txt")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(content)
                logging.info(f"Contenu texte sauvegardé: {url} -> {filepath}")
        except Exception as e:
            logging.error(f"Erreur sauvegarde {url}: {str(e)}")

    def handle_result(self, content_type, url, content):
        try:
            normalized_url = self.url_processor.normalize_url(url)
            if normalized_url not in self.seen_urls:
                self.seen_urls.add(normalized_url)
                self.save_content(url, content_type, content)
                
                if content_type == 'html':
                    self.queue_new_links(url)
        except Exception as e:
            logging.error(f"Erreur traitement résultat {url}: {str(e)}")

    def queue_new_links(self, url):
        try:
            response = self.safe_request(url)
            links = self.content_extractor.extract_links(response.content, url)
            
            for link in links:
                normalized_link = self.url_processor.normalize_url(link)
                if normalized_link not in self.seen_urls and self.url_processor.should_process_url(link):
                    self.queue.append(link)
        except Exception as e:
            logging.error(f"Erreur extraction liens {url}: {str(e)}")

    def crawl(self):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config['crawler']['max_workers']
        ) as executor:
            while self.queue and len(self.seen_urls) < self.config['crawler']['max_queue_size']:
                try:
                    urls_batch = []
                    for _ in range(min(self.config['crawler']['max_workers'], len(self.queue))):
                        if self.queue:
                            urls_batch.append(self.queue.popleft())

                    futures = {executor.submit(self.process_url, url): url for url in urls_batch}
                    
                    for future in concurrent.futures.as_completed(futures):
                        url = futures[future]
                        try:
                            result = future.result()
                            if result:
                                self.handle_result(*result)
                                self.step_counter += 1
                                # Tous les 5 pas, afficher l'ASCII art
                                if self.step_counter % 60 == 0:
                                    self.display_ascii_art()
                        except Exception as e:
                            logging.error(f"Erreur traitement {url}: {str(e)}")

                    time.sleep(random.uniform(
                        self.config['crawler']['delay_min'],
                        self.config['crawler']['delay_max']
                    ))

                except Exception as e:
                    logging.error(f"Erreur boucle principale: {str(e)}")
                    continue

    def display_ascii_art(self):
        ascii_art = pyfiglet.figlet_format("Your crawling is in process")
        print(ascii_art)
