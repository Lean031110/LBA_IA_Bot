import logging
import sys
from datetime import datetime
from pathlib import Path
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
        logging.FileHandler(f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Función principal del bot"""
    try:
        # Inicializar componentes principales
        database = Database()
        bot_brain = BotBrain()

        # Crear directorios necesarios
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("data/backups").mkdir(exist_ok=True)

        # Inicializar handlers
        basic_handler = BasicHandler(bot_brain)
        admin_handler = AdminHandler(bot_brain)
        group_handler = GroupHandler(bot_brain)
        search_handler = SearchHandler()

        # Inicializar la aplicación
        application = Application.builder().token(Config.BOT_TOKEN).build()

        # Registrar handlers básicos
        application.add_handler(CommandHandler("start", basic_handler.start))
        application.add_handler(CommandHandler("help", basic_handler.help))
        application.add_handler(CommandHandler("info", basic_handler.info))

        # Registrar handlers de búsqueda
        application.add_handler(CommandHandler("search", search_handler.search))
        application.add_handler(CommandHandler("wiki", search_handler.wiki))

        # Registrar handlers de administración
        application.add_handler(CommandHandler("config", admin_handler.config))
        application.add_handler(CommandHandler("stats", admin_handler.stats))
        application.add_handler(CommandHandler("train", admin_handler.train))
        application.add_handler(CommandHandler("backup", admin_handler.backup))
        application.add_handler(CommandHandler("broadcast", admin_handler.broadcast))

        # Registrar handlers de grupo
        application.add_handler(CommandHandler("welcome", group_handler.set_welcome))
        application.add_handler(CommandHandler("rules", group_handler.set_rules))
        application.add_handler(CommandHandler("warn", group_handler.warn))
        application.add_handler(CommandHandler("unwarn", group_handler.unwarn))
        application.add_handler(CommandHandler("ban", group_handler.ban))
        application.add_handler(CommandHandler("unban", group_handler.unban))

        # Registrar handler para callbacks de botones
        application.add_handler(CallbackQueryHandler(basic_handler.handle_callback))

        # Registrar handler para mensajes normales
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            basic_handler.handle_message
        ))

        # Registrar handler para nuevos miembros
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            group_handler.welcome_new_member
        ))

        # Iniciar el bot
        logger.info("Bot iniciado correctamente")
        await application.initialize()
        await application.start()
        await application.run_polling()

    except Exception as e:
        logger.error(f"Error iniciando el bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())