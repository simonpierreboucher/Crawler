# src/file_handler.py
from pathlib import Path
import os
import hashlib
import logging
from urllib.parse import urlparse
import mimetypes
import string

class FileHandler:
    """Gère le téléchargement et l'organisation des fichiers"""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.files_dir = os.path.join(self.output_dir, 'files')
        self.downloadable_extensions = {
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
            'presentation': ['.ppt', '.pptx', '.odp'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'video': ['.mp4', '.avi', '.mkv', '.mov'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.h'],
            'data': ['.json', '.xml', '.yaml', '.sql'],
            'ebook': ['.epub', '.mobi', '.azw'],
            'other': []
        }
        self._setup_directories()
    
    def _setup_directories(self):
        """Crée les sous-répertoires pour chaque catégorie de fichiers"""
        for category in self.downloadable_extensions.keys():
            category_dir = os.path.join(self.files_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            logging.info(f"Répertoire pour la catégorie '{category}' créé: {category_dir}")
    
    def get_file_category(self, url):
        """Détermine la catégorie d'un fichier basé sur son extension"""
        ext = Path(urlparse(url).path).suffix.lower()
        for category, extensions in self.downloadable_extensions.items():
            if ext in extensions:
                return category
        return 'other'
    
    def is_downloadable_file(self, url):
        """Vérifie si l'URL pointe vers un fichier téléchargeable"""
        return self.get_file_category(url) is not None
    
    def generate_safe_filename(self, url, category):
        """Génère un nom de fichier unique et sécurisé"""
        original_filename = os.path.basename(urlparse(url).path)
        
        if not original_filename:
            filename_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            ext = mimetypes.guess_extension(url) or '.unknown'
            original_filename = f"{filename_hash}{ext}"
        
        # Nettoyage du nom de fichier
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in original_filename if c in valid_chars)
        if len(filename) > 100:
            filename = filename[:100]
        
        # Assurer l'unicité
        unique_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{filename}_{unique_hash}"
        
        # Ajout de l'extension correcte
        ext = Path(original_filename).suffix
        filename = f"{filename}{ext}"
        
        return filename
