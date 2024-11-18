from src.constants import *
import click
from src.utils import load_config, setup_logging
from src.session import SafeSession
from src.extractors import ContentExtractor
from src.processors import URLProcessor
from src.crawler import SafeCrawler
import os
import logging
import sys
import pyfiglet  # Import de pyfiglet

# Affichage de l'ASCII art au début du script
ascii_art = pyfiglet.figlet_format("M-LAI")
print(ascii_art)

@click.command()
@click.option('--config', '-c', default='config/settings.yaml', help='Chemin du fichier de configuration')
@click.option('--output', '-o', default='output', help='Dossier de sortie')
@click.option('--resume', '-r', is_flag=True, help='Reprendre un crawl précédent')
def main(config, output, resume):
    """Programme principal du crawler web"""
    try:
        # Charge la configuration
        config_data = load_config(config)
        
        # Configure le logging
        setup_logging(config_data)
        
        # Log les paramètres de démarrage
        logging.info(f"Démarrage du crawler avec config: {config}")
        logging.info(f"Dossier de sortie: {output}")
        logging.info(f"Mode reprise: {resume}")
        
        # Crée le dossier de sortie
        output_dir = os.path.join(output, config_data['files']['output_dir'], config_data['domain']['name'])
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Dossier de sortie créé: {output_dir}")
        
        # Initialise les composants
        try:
            session = SafeSession.create(config_data)
            logging.info("Session HTTP initialisée")
            
            content_extractor = ContentExtractor()
            logging.info("Extracteur de contenu initialisé")
            
            url_processor = URLProcessor(config_data)
            logging.info("Processeur d'URL initialisé")
            
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation des composants: {str(e)}")
            raise
        
        # Initialise et lance le crawler
        try:
            crawler = SafeCrawler(config_data, session, content_extractor, url_processor, output_dir, resume)
            logging.info("Crawler initialisé")
            
            crawler.crawl()
            logging.info("Crawling terminé avec succès")
            
        except Exception as e:
            logging.error(f"Erreur lors du crawling: {str(e)}")
            raise
            
        click.echo("Crawling terminé avec succès")
        
    except Exception as e:
        logging.error(f"Erreur critique: {str(e)}")
        click.echo(f"Erreur critique: {str(e)}", err=True)
        sys.exit(1)
    finally:
        # Sauvegarde l'état final si le crawler a été initialisé
        if 'crawler' in locals():
            try:
                crawler.save_state()
                logging.info("État final sauvegardé")
            except Exception as e:
                logging.error(f"Erreur lors de la sauvegarde de l'état final: {str(e)}")

if __name__ == '__main__':
    main()
