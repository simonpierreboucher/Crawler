# src/utils.py
from src.constants import *
import yaml
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys
import os

def load_config(config_path="config/settings.yaml"):
    """Charge la configuration depuis le fichier YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        raise

def setup_logging(config):
    """Configure le système de logging avec des handlers multiples et des formats avancés"""
    try:
        log_dir = config['files'].get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'crawler_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # Création d'un logger personnalisé
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Format commun
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
        )
        
        # Handler pour le fichier avec rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config['files']['max_log_size'],
            backupCount=config['files']['max_log_backups']
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler pour la console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logging.info("Configuration du logging terminée")
    except Exception as e:
        print(f"Erreur lors de la configuration du logging: {str(e)}")
        raise
