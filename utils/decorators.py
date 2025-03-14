import logging
import functools
from datetime import datetime
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def log_command(f: Callable) -> Callable:
    """Decorador para registrar el uso de comandos"""
    @functools.wraps(f)
    async def decorated(self: Any, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        chat = update.effective_chat
        command = update.effective_message.text if update.effective_message else "No message"

        # Registrar el uso del comando
        logger.info(
            f"Command: {command} | "
            f"User: {user.username} ({user.id}) | "
            f"Chat: {chat.title if chat.title else 'Private'} ({chat.id}) | "
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            return await f(self, update, context)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            await update.effective_message.reply_text(
                "❌ Ha ocurrido un error al procesar el comando. Por favor, inténtalo de nuevo."
            )
    return decorated

def admin_only(f: Callable) -> Callable:
    """Decorador para restringir comandos solo a administradores"""
    @functools.wraps(f)
    async def decorated(self: Any, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if user.id != int(self.config.CREATOR_ID):
            await update.effective_message.reply_text(
                "⚠️ Este comando solo está disponible para administradores."
            )
            return
        return await f(self, update, context)
    return decorated

def group_only(f: Callable) -> Callable:
    """Decorador para restringir comandos solo a grupos"""
    @functools.wraps(f)
    async def decorated(self: Any, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        chat = update.effective_chat
        if chat.type == 'private':
            await update.effective_message.reply_text(
                "⚠️ Este comando solo está disponible en grupos."
            )
            return
        return await f(self, update, context)
    return decorated

def rate_limit(limit: int = 5, window: int = 60) -> Callable:
    """Decorador para limitar la frecuencia de uso de comandos"""
    def decorator(f: Callable) -> Callable:
        USAGE = {}

        @functools.wraps(f)
        async def decorated(self: Any, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            user_id = update.effective_user.id
            current_time = datetime.now().timestamp()

            # Limpiar registros antiguos
            USAGE[user_id] = [t for t in USAGE.get(user_id, [])
                            if current_time - t < window]

            # Verificar límite
            if len(USAGE.get(user_id, [])) >= limit:
                await update.effective_message.reply_text(
                    f"⚠️ Has excedido el límite de uso. "
                    f"Intenta de nuevo en {window} segundos."
                )
                return

            # Registrar uso
            if user_id not in USAGE:
                USAGE[user_id] = []
            USAGE[user_id].append(current_time)

            return await f(self, update, context)
        return decorated
    return decorator