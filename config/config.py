import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración principal del bot"""

    # Información del Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'LBAIABot')
    BOT_NAME = "LBA IA Bot"
    BOT_VERSION = "1.0.0"
    CREATOR_ID = int(os.getenv('CREATOR_ID', '0'))
    CREATOR_USERNAME = "@Lean031110"

    # Base de datos
    DB_FILE = 'data/bot_data.db'

    # Configuración de IA
    LEARNING_RATE = float(os.getenv('LEARNING_RATE', '0.01'))
    MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.7'))
    MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', '1000'))

    # Límites y Moderación
    SPAM_THRESHOLD = 5  # Mensajes
    FLOOD_TIME_WINDOW = 60  # Segundos
    MAX_WARNINGS = 3
    MUTE_DURATION = 300  # 5 minutos en segundos
    MAX_MESSAGE_LENGTH = 4096

    # Rutas
    BACKUP_DIR = 'data/backups'
    LOG_DIR = 'logs'
    TEMP_DIR = 'temp'

    # Comandos disponibles
    COMMANDS = {
        'start': 'Iniciar el bot',
        'help': 'Mostrar ayuda',
        'info': 'Información del bot',
        'search': 'Buscar información',
        'wiki': 'Buscar en Wikipedia',
        'config': 'Configuración (admin)',
        'stats': 'Estadísticas (admin)',
        'train': 'Entrenar IA (admin)',
        'backup': 'Crear respaldo (admin)',
        'broadcast': 'Enviar mensaje masivo (admin)'
    }

    # Mensajes predefinidos
    MESSAGES = {
        'welcome': """¡Hola {name}! 👋

Soy {bot_name}, un bot de IA diseñado para ayudarte. 🤖

Puedo:
• Responder preguntas 💭
• Buscar información 🔍
• Moderar grupos 👥
• Aprender de las conversaciones 🧠

Usa /help para ver todos los comandos disponibles.""",

        'help': """📚 *Comandos Disponibles*

*Comandos Básicos:*
/start - Iniciar el bot
/help - Mostrar esta ayuda
/info - Información del bot
/search - Buscar información
/wiki - Buscar en Wikipedia

*Comandos de Admin:*
/config - Panel de configuración
/stats - Ver estadísticas
/train - Entrenar la IA
/backup - Crear respaldo
/broadcast - Enviar mensaje masivo

Para más información, contacta a {creator_username}""",

        'error': "❌ Ha ocurrido un error: {error}",

        'no_permission': "⚠️ No tienes permiso para usar este comando.",

        'rate_limit': "⚠️ Has excedido el límite de uso. Intenta de nuevo en {time} segundos.",

        'command_disabled': "⚠️ Este comando está temporalmente deshabilitado.",
    }

    # Configuración de respaldo
    BACKUP_CONFIG = {
        'auto_backup': True,
        'backup_interval': 24,  # Horas
        'max_backups': 7,  # Mantener últimos 7 respaldos
    }

    # Configuración de logging
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
                'mode': 'a',
            },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['default', 'file'],
                'level': 'INFO',
                'propagate': True
            },
        }
    }

    @classmethod
    def get_command_list(cls) -> list:
        """Retorna la lista de comandos para BotFather"""
        return [f"{cmd} - {desc}" for cmd, desc in cls.COMMANDS.items()]

    @classmethod
    def format_message(cls, message_key: str, **kwargs) -> str:
        """Formatea un mensaje predefinido con los parámetros dados"""
        try:
            message = cls.MESSAGES[message_key]
            return message.format(
                bot_name=cls.BOT_NAME,
                creator_username=cls.CREATOR_USERNAME,
                **kwargs
            )
        except KeyError:
            return f"Message template '{message_key}' not found"
        except Exception as e:
            return f"Error formatting message: {str(e)}"

class Config_Web:
    """Configuración específica para la aplicación web"""
    
    # Configuración específica de la web
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///data/web_data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
