import logging
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

class Bot:
    def __init__(self):
        """Inicialización del bot"""
        self.application = None
        self.database = None
        self.bot_brain = None
        self.logger = logging.getLogger(__name__)
        self._running = False

    async def initialize_bot(self) -> None:
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

    async def register_handlers(self, *handlers) -> None:
        """Registra todos los handlers del bot"""
        try:
            basic_handler, admin_handler, group_handler, search_handler = handlers

            # [El código de registro de handlers permanece igual]
            # ... (mantén el código de registro de handlers que ya tenías)

            self.logger.info("All handlers registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering handlers: {e}")
            raise

    async def start(self) -> None:
        """Inicia el bot"""
        try:
            await self.initialize_bot()
            self.logger.info("Starting bot...")

            await self.application.initialize()
            self._running = True

            async with self.application:
                await self.application.start()
                await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            self._running = False
            self.logger.info("Stopping bot...")
            try:
                if self.application:
                    await self.application.stop()
                    await self.application.shutdown()
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")