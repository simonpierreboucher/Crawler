from src.constants import *
import yaml

def load_config(config_path="config/settings.yaml"):
    """Charge la configuration depuis le fichier YAML"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        raise

def setup_logging(config):
    """Configure le système de logging"""
    try:
        log_file = f'crawler_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
            handlers=[
                RotatingFileHandler(
                    log_file,
                    maxBytes=config['files']['max_log_size'],
                    backupCount=config['files']['max_log_backups']
                ),
                logging.StreamHandler(sys.stdout)
            ]
        )
    except Exception as e:
        print(f"Erreur lors de la configuration du logging: {str(e)}")
        raise
