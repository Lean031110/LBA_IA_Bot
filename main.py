import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from config.config import Config
from handlers.basic_handler import BasicHandler
from handlers.admin_handler import AdminHandler
from handlers.group_handler import GroupHandler
from handlers.search_handler import SearchHandler
from core.bot_brain import BotBrain
from core.database import Database

# Configurar directorio de logs
Path("logs").mkdir(exist_ok=True)

# Configuración del logging
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

# Configurar logging
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        """Inicialización del bot"""
        self.application = None
        self.database = None
        self.bot_brain = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Inicializa todos los componentes del bot"""
        try:
            # Crear directorios necesarios
            for directory in ["logs", "data", "data/backups"]:
                Path(directory).mkdir(exist_ok=True)

            # Inicializar componentes principales
            self.database = Database()
            self.bot_brain = BotBrain()

            # Inicializar handlers
            basic_handler = BasicHandler(self.bot_brain)
            admin_handler = AdminHandler(self.bot_brain)
            group_handler = GroupHandler(self.bot_brain)
            search_handler = SearchHandler()

            # Construir la aplicación
            self.application = (
                Application.builder()
                .token(Config.BOT_TOKEN)
                .build()
            )

            # Registrar handlers
            await self.register_handlers(
                basic_handler,
                admin_handler,
                group_handler,
                search_handler
            )

            self.logger.info("Bot initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing bot: {e}")
            raise

    async def register_handlers(
        self,
        basic_handler: BasicHandler,
        admin_handler: AdminHandler,
        group_handler: GroupHandler,
        search_handler: SearchHandler
    ) -> None:
        """Registra todos los handlers del bot"""
        try:
            # Handlers básicos
            self.application.add_handler(CommandHandler("start", basic_handler.start))
            self.application.add_handler(CommandHandler("help", basic_handler.help))
            self.application.add_handler(CommandHandler("info", basic_handler.info))

            # Handlers de búsqueda
            self.application.add_handler(CommandHandler("search", search_handler.search))
            self.application.add_handler(CommandHandler("wiki", search_handler.wiki))

            # Handlers de administración
            self.application.add_handler(CommandHandler("config", admin_handler.config))
            self.application.add_handler(CommandHandler("stats", admin_handler.stats))
            self.application.add_handler(CommandHandler("train", admin_handler.train))
            self.application.add_handler(CommandHandler("backup", admin_handler.backup))
            self.application.add_handler(CommandHandler("broadcast", admin_handler.broadcast))

            # Handlers de grupo
            self.application.add_handler(CommandHandler("welcome", group_handler.set_welcome))
            self.application.add_handler(CommandHandler("rules", group_handler.set_rules))
            self.application.add_handler(CommandHandler("warn", group_handler.warn))
            self.application.add_handler(CommandHandler("unwarn", group_handler.unwarn))
            self.application.add_handler(CommandHandler("ban", group_handler.ban))
            self.application.add_handler(CommandHandler("unban", group_handler.unban))

            # Handler para callbacks
            self.application.add_handler(CallbackQueryHandler(basic_handler.handle_callback))

            # Handler para mensajes normales
            self.application.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    basic_handler.handle_message
                )
            )

            # Handler para nuevos miembros
            self.application.add_handler(
                MessageHandler(
                    filters.StatusUpdate.NEW_CHAT_MEMBERS,
                    group_handler.handle_new_members
                )
            )

            # Handler para errores
            self.application.add_error_handler(self.error_handler)

            self.logger.info("All handlers registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering handlers: {e}")
            raise

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja los errores del bot"""
        self.logger.error(f"Update {update} caused error {context.error}")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "Lo siento, ha ocurrido un error. Por favor, intenta más tarde."
                )
        except Exception as e:
            self.logger.error(f"Error sending error message: {e}")

    async def start(self) -> None:
        """Inicia el bot"""
        try:
            await self.initialize()
            self.logger.info("Starting bot...")
            await self.application.start()
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            if self.application:
                await self.application.stop()

def main() -> None:
    """Función principal"""
    try:
        import asyncio
        bot = Bot()
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()