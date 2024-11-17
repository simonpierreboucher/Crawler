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
        if not self.resume:
            self.load_state()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logging.info("Arrêt gracieux du crawler...")
        self.save_state()
        sys.exit(0)

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
        except Exception as e:
            logging.error(f"Erreur chargement état: {str(e)}")

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
            except Exception as e:
                if attempt == self.config['timeouts']['max_retries'] - 1:
                    raise
                logging.warning(f"Retrying {url} ({attempt + 1}/{self.config['timeouts']['max_retries']}) due to error: {str(e)}")
                time.sleep(2 ** attempt)

    def process_url(self, url):
        try:
            if not self.url_processor.should_process_url(url):
                return None

            response = self.safe_request(url)
            
            if response.status_code == 404:
                logging.warning(f"Page non trouvée: {url}")
                return None

            content_type = response.headers.get('Content-Type', '').lower()

            if 'application/pdf' in content_type:
                return self.process_pdf(response, url)
            elif 'text/html' in content_type:
                return self.process_html(response, url)

        except Exception as e:
            logging.error(f"Erreur traitement {url}: {str(e)}")
            return None

    def process_pdf(self, response, url):
        try:
            pdf_content = self.content_extractor.extract_text_from_pdf(response.content)
            return ('pdf', url, pdf_content) if pdf_content.strip() else None
        except Exception as e:
            logging.error(f"Erreur PDF {url}: {str(e)}")
            return None

    def process_html(self, response, url):
        try:
            text = self.content_extractor.extract_text_from_html(response.content)
            if not text.strip():
                text = self.content_extractor.extract_text_alternative(response.content)
            return ('html', url, text) if text.strip() else None
        except Exception as e:
            logging.error(f"Erreur HTML {url}: {str(e)}")
            return None

    def save_content(self, url, content_type, content):
        """Sauvegarde le contenu extrait avec métadonnées"""
        try:
            filename = self.url_processor.sanitize_filename(url)
            filepath = os.path.join(self.output_dir, f"{filename}.txt")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Prépare le contenu avec métadonnées
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_content = f"""URL: {url}
Timestamp: {timestamp}
Content Type: {content_type}
{'=' * 100}

{content}

{'=' * 100}
End of content from: {url}"""
            
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(formatted_content)
            logging.info(f"Contenu sauvegardé: {url}")
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
        if not self.resume:
            self.queue.append(self.config['domain']['start_url'])
        
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
                        except Exception as e:
                            logging.error(f"Erreur traitement {url}: {str(e)}")

                    time.sleep(random.uniform(
                        self.config['crawler']['delay_min'],
                        self.config['crawler']['delay_max']
                    ))

                except Exception as e:
                    logging.error(f"Erreur boucle principale: {str(e)}")
                    continue
