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

# Configurar logging con UTC
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.utcnow().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def shutdown(application: Application):
    """Cierra la aplicación de manera segura"""
    try:
        await application.stop()
        await application.shutdown()
    except Exception as e:
        logger.error(f"Error durante el cierre: {e}")

async def main():
    """Función principal del bot"""
    application = None
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

        # Inicializar la aplicación sin configuración de zona horaria
        application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .concurrent_updates(True)  # Permitir actualizaciones concurrentes
            .connection_pool_size(8)   # Aumentar el tamaño del pool de conexiones
            .build()
        )

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

        # Ejecutar el polling sin especificar zona horaria
        await application.run_polling(
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
        if application:
            await shutdown(application)
        raise  # Esto nos permitirá ver el error completo

def run_bot():
    """Ejecuta el bot con manejo apropiado del event loop"""
    try:
        import asyncio

        # Configurar el event loop
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Usar run directamente en lugar de manipular el loop manualmente
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_bot()