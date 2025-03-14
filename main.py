import sys
import asyncio
from config.logging_config import setup_logging
from core.bot import Bot

logger = setup_logging()

def setup_asyncio():
    """Configura el entorno asyncio"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

def main() -> None:
    """Función principal"""
    try:
        loop = setup_asyncio()
        bot = Bot()
        loop.run_until_complete(bot.start())

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        try:
            loop.close()
        except Exception as e:
            logger.error(f"Error closing event loop: {e}")

if __name__ == '__main__':
    main()