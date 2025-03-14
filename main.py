import logging
import sys
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config.config import Config
from handlers.basic_handler import BasicHandler
from handlers.admin_handler import AdminHandler
from handlers.group_handler import GroupHandler
from handlers.search_handler import SearchHandler
from core.bot_brain import BotBrain
from core.database import Database

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.utcnow().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        self.application = None
        self.database = None
        self.bot_brain = None

    async def initialize(self):
        """Inicializa todos los componentes del bot"""
        # Crear directorios necesarios
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("data/backups").mkdir(exist_ok=True)

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
        self.register_handlers(
            basic_handler,
            admin_handler,
            group_handler,
            search_handler
        )

    def register_handlers(self, basic_handler, admin_handler, group_handler, search_handler):
        """Registra todos los handlers de la aplicación"""
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
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            basic_handler.handle_message
        ))

        # Handler para nuevos miembros
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            group_handler.welcome_new_member
        ))

    async def start(self):
        """Inicia el bot"""
        try:
            await self.initialize()
            logger.info("Bot iniciado correctamente")
            await self.application.initialize()
            await self.application.start()
            await self.application.run_polling(
                allowed_updates=[
                    "message",
                    "edited_message",
                    "callback_query",
                    "chat_member"
                ],
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Error iniciando el bot: {e}")
            if self.application:
                await self.application.shutdown()
            raise

async def main():
    """Función principal"""
    bot = Bot()
    await bot.start()

def run_bot():
    """Ejecuta el bot"""
    import asyncio

    try:
        # Configurar para Windows si es necesario
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Ejecutar el bot
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_bot()