# src/session.py
from src.constants import *
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from fake_useragent import UserAgent
import requests
import logging

class SafeSession:
    """Classe gérant les sessions HTTP de manière sécurisée"""
    
    @staticmethod
    def create(config):
        try:
            session = requests.Session()
            retry_strategy = Retry(
                total=config['timeouts']['max_retries'],
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                raise_on_status=False  # Modifier pour ne pas lever d'exception sur certains statuts
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            session.headers.update({
                'User-Agent': UserAgent().random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            })
            
            # Désactive la vérification SSL
            session.verify = False
            
            return session
        except Exception as e:
            logging.error(f"Erreur lors de la création de la session: {str(e)}")
            raise
