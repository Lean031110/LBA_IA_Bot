from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
import asyncio

class GroupHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain
        self.spam_counter = {}
        self.user_warnings = {}

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja los mensajes en grupos"""
        if not update.message:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        # Verificar spam
        if await self.is_spam(chat_id, user_id):
            await self.handle_spam(update, context)
            return

        # Verificar contenido inapropiado
        if await self.check_inappropriate_content(update.message.text):
            await self.handle_inappropriate_content(update, context)
            return

        # Procesar mensaje normal
        await self.process_group_message(update, context)

    async def is_spam(self, chat_id: int, user_id: int) -> bool:
        """Detecta si un usuario está haciendo spam"""
        key = f"{chat_id}:{user_id}"
        current_time = asyncio.get_event_loop().time()

        if key not in self.spam_counter:
            self.spam_counter[key] = {
                'count': 1,
                'first_message': current_time
            }
            return False

        # Resetear contador si ha pasado el tiempo de ventana
        if current_time - self.spam_counter[key]['first_message'] > Config.FLOOD_TIME_WINDOW:
            self.spam_counter[key] = {
                'count': 1,
                'first_message': current_time
            }
            return False

        self.spam_counter[key]['count'] += 1
        return self.spam_counter[key]['count'] > Config.SPAM_THRESHOLD

    async def handle_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja casos de spam"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        if user_id not in self.user_warnings:
            self.user_warnings[user_id] = 0

        self.user_warnings[user_id] += 1

        warning_text = (
            f"⚠️ @{update.effective_user.username} por favor evita el spam. "
            f"Advertencia {self.user_warnings[user_id]}/{Config.MAX_WARNINGS}"
        )

        await update.message.reply_text(warning_text)

        if self.user_warnings[user_id] >= Config.MAX_WARNINGS:
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                await update.message.reply_text(
                    f"🚫 Usuario baneado por múltiples advertencias de spam."
                )
            except Exception as e:
                await update.message.reply_text(
                    "❌ No tengo permisos suficientes para banear usuarios."
                )

    async def check_inappropriate_content(self, text: str) -> bool:
        """Verifica si el contenido es inapropiado"""
        if not text:
            return False

        inappropriate_words = [
            # Lista de palabras inapropiadas
            # Se puede cargar desde una base de datos o archivo
        ]

        return any(word in text.lower() for word in inappropriate_words)

    async def process_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Procesa mensajes normales en grupos"""
        # Aquí puedes implementar lógica adicional para procesar mensajes
        # Por ejemplo, responder a menciones del bot
        if context.bot.username in update.message.text:
            response = await self.bot_brain.process_message(
                update.message.text,
                update.effective_user.id
            )
            if response:
                await update.message.reply_text(response)