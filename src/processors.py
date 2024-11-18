# src/processors.py
from src.constants import *
import string
import hashlib
import unicodedata
import os
from urllib.parse import urlparse
import logging

class URLProcessor:
    """Classe gérant le traitement des URLs"""
    
    def __init__(self, config):
        self.config = config
    
    def sanitize_filename(self, url):
        try:
            # Génère un hash MD5 de l'URL complète
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
            
            # Extraire le dernier segment du chemin de l'URL
            parsed = urlparse(url)
            path = parsed.path.strip('/').split('/')[-1]  # Prendre uniquement le dernier segment
            if not path:
                path = "home"
            
            # Supprimer l'extension si c'est un PDF ou une image
            if path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                path = os.path.splitext(path)[0]
            
            # Normalise et nettoie le nom
            path = unicodedata.normalize('NFKD', path).encode('ASCII', 'ignore').decode('ASCII')
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            path = ''.join(c for c in path if c in valid_chars)
            
            # Limite la longueur du chemin simplifié
            max_path_length = 50  # Ajustez selon vos besoins
            if len(path) > max_path_length:
                path = path[:max_path_length]
            
            # Combine le chemin simplifié avec le hash pour garantir l'unicité
            filename = f"{path}_{url_hash}"
            
            # Limite la longueur totale du nom de fichier
            max_total_length = self.config['files']['max_length']
            if len(filename) > max_total_length:
                # Troncature supplémentaire si nécessaire
                excess_length = len(filename) - max_total_length
                filename = f"{filename[:-excess_length]}_{url_hash[:4]}"
            
            return filename
        except Exception as e:
            logging.error(f"Erreur lors de la sanitization du nom de fichier: {str(e)}")
            # Génère un nom par défaut avec hash
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
            return f"default_{url_hash}"
    
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
