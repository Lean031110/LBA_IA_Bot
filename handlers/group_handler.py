from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
import asyncio
from utils.decorators import admin_only, log_command

class GroupHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain
        self.spam_counter = {}
        self.user_warnings = {}
        self.welcome_messages = {}
        self.group_rules = {}

    @admin_only
    @log_command
    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Configura el mensaje de bienvenida para el grupo"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /welcome Mensaje de bienvenida\n"
                "Puedes usar {username} para mencionar al nuevo usuario."
            )
            return

        chat_id = update.effective_chat.id
        welcome_message = ' '.join(context.args)
        self.welcome_messages[chat_id] = welcome_message

        await update.message.reply_text(
            "✅ Mensaje de bienvenida configurado exitosamente.\n"
            f"Mensaje: {welcome_message}"
        )

    @admin_only
    @log_command
    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Configura las reglas del grupo"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /rules Las reglas del grupo\n"
                "Separa las reglas con puntos o nuevas líneas."
            )
            return

        chat_id = update.effective_chat.id
        rules = ' '.join(context.args)
        self.group_rules[chat_id] = rules

        await update.message.reply_text(
            "✅ Reglas del grupo configuradas exitosamente.\n"
            f"Reglas:\n{rules}"
        )

    @admin_only
    @log_command
    async def warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Advierte a un usuario"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /warn @usuario razón"
            )
            return

        # Obtener el usuario mencionado
        try:
            user = await context.bot.get_chat_member(
                update.effective_chat.id,
                context.args[0]
            )
            reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Sin razón especificada"

            user_id = user.user.id
            if user_id not in self.user_warnings:
                self.user_warnings[user_id] = 0

            self.user_warnings[user_id] += 1

            await update.message.reply_text(
                f"⚠️ {user.user.username} ha sido advertido.\n"
                f"Razón: {reason}\n"
                f"Advertencias: {self.user_warnings[user_id]}/{Config.MAX_WARNINGS}"
            )

            if self.user_warnings[user_id] >= Config.MAX_WARNINGS:
                await self.ban(update, context)

        except Exception as e:
            await update.message.reply_text(
                "❌ Error al advertir al usuario. Asegúrate de mencionar a un usuario válido."
            )

    @admin_only
    @log_command
    async def unwarn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Quita una advertencia a un usuario"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /unwarn @usuario"
            )
            return

        try:
            user = await context.bot.get_chat_member(
                update.effective_chat.id,
                context.args[0]
            )
            user_id = user.user.id

            if user_id in self.user_warnings and self.user_warnings[user_id] > 0:
                self.user_warnings[user_id] -= 1
                await update.message.reply_text(
                    f"✅ Se ha quitado una advertencia a {user.user.username}\n"
                    f"Advertencias restantes: {self.user_warnings[user_id]}/{Config.MAX_WARNINGS}"
                )
            else:
                await update.message.reply_text(
                    "ℹ️ Este usuario no tiene advertencias."
                )

        except Exception as e:
            await update.message.reply_text(
                "❌ Error al quitar la advertencia. Asegúrate de mencionar a un usuario válido."
            )

    @admin_only
    @log_command
    async def ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Banea a un usuario del grupo"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /ban @usuario razón"
            )
            return

        try:
            user = await context.bot.get_chat_member(
                update.effective_chat.id,
                context.args[0]
            )
            reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Sin razón especificada"

            await context.bot.ban_chat_member(
                update.effective_chat.id,
                user.user.id
            )

            await update.message.reply_text(
                f"🚫 Usuario {user.user.username} baneado.\n"
                f"Razón: {reason}"
            )

        except Exception as e:
            await update.message.reply_text(
                "❌ Error al banear al usuario. Verifica mis permisos y que el usuario sea válido."
            )

    @admin_only
    @log_command
    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Desbanea a un usuario del grupo"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /unban @usuario"
            )
            return

        try:
            user = await context.bot.get_chat_member(
                update.effective_chat.id,
                context.args[0]
            )

            await context.bot.unban_chat_member(
                update.effective_chat.id,
                user.user.id
            )

            await update.message.reply_text(
                f"✅ Usuario {user.user.username} desbaneado."
            )

        except Exception as e:
            await update.message.reply_text(
                "❌ Error al desbanear al usuario. Verifica mis permisos y que el usuario sea válido."
            )

    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Da la bienvenida a nuevos miembros"""
        if not update.message.new_chat_members:
            return

        chat_id = update.effective_chat.id
        for new_member in update.message.new_chat_members:
            if new_member.is_bot:
                continue

            welcome_msg = self.welcome_messages.get(
                chat_id,
                "👋 ¡Bienvenido/a {username} al grupo!"
            )

            await update.message.reply_text(
                welcome_msg.format(username=new_member.username or new_member.first_name)
            )

            if chat_id in self.group_rules:
                await update.message.reply_text(
                    "📜 *Reglas del grupo:*\n" + self.group_rules[chat_id],
                    parse_mode='Markdown'
                )

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
        if context.bot.username in update.message.text:
            response = await self.bot_brain.process_message(
                update.message.text,
                update.effective_user.id
            )
            if response:
                await update.message.reply_text(response)

    async def handle_inappropriate_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja contenido inapropiado"""
        await update.message.reply_text(
            "⚠️ Por favor, mantén un lenguaje apropiado en el grupo."
        )
        # Aquí puedes implementar más acciones como eliminar el mensaje o advertir al usuario