import logging
import logging.config
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Configura y retorna la configuración del logging"""
    Path("logs").mkdir(exist_ok=True)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': f"logs/bot_{datetime.utcnow().strftime('%Y%m%d')}.log",
                'formatter': 'standard'
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(logging_config)
    return logging.getLogger(__name__)