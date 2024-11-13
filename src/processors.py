from src.constants import *
import string
import hashlib

class URLProcessor:
    """Classe gérant le traitement des URLs"""
    
    def __init__(self, config):
        self.config = config
    
    def sanitize_filename(self, filename):
        try:
            # Crée un hash du nom complet
            filename_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
            
            # Normalise et nettoie le nom
            filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            filename = ''.join(c for c in filename if c in valid_chars)
            
            # Tronque si nécessaire
            max_length = self.config['files']['max_length']
            name, ext = os.path.splitext(filename)
            if len(filename) > max_length:
                return f"{name[:max_length-12]}_{filename_hash}{ext}"
            return filename
        except Exception as e:
            logging.error(f"Erreur lors de la sanitization du nom de fichier: {str(e)}")
            return f"default_{filename_hash}"

    def normalize_url(self, url):
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception as e:
            logging.error(f"Erreur lors de la normalisation de l'URL: {str(e)}")
            return url

    def is_valid_url(self, url):
        if not url or len(url) > self.config['files']['max_url_length']:
            return False
            
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme,
                parsed.netloc,
                parsed.scheme in ['http', 'https'],
                self.config['domain']['name'] in parsed.netloc
            ])
        except Exception as e:
            logging.error(f"Erreur lors de la validation de l'URL: {str(e)}")
            return False

    def should_process_url(self, url):
        if not url:
            return False
            
        try:
            lower_url = url.lower()
            
            # Vérifie les patterns exclus
            if any(pattern in lower_url for pattern in self.config['excluded']['patterns']):
                return False
                
            # Vérifie les extensions exclues
            if any(lower_url.endswith(ext) for ext in self.config['excluded']['extensions']):
                return False
                
            return self.is_valid_url(url)
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de l'URL: {str(e)}")
            return False
