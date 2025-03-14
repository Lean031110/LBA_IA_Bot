from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
from utils.decorators import group_only, admin_only, log_command
import logging

class GroupHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain
        self.logger = logging.getLogger(__name__)

    @group_only
    @log_command
    async def handle_new_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja la entrada de nuevos miembros al grupo"""
        try:
            chat = update.effective_chat
            new_members = update.message.new_chat_members

            for new_member in new_members:
                if new_member.id == context.bot.id:
                    # Si el nuevo miembro es el bot
                    await update.message.reply_text(
                        "¡Hola! Gracias por añadirme al grupo. "
                        "Usa /help para ver mis comandos disponibles."
                    )
                else:
                    # Si es un nuevo usuario
                    welcome_message = (
                        f"¡Bienvenido/a {new_member.mention_html()} al grupo "
                        f"{chat.title}! 👋\n\n"
                        "Por favor, lee las reglas del grupo usando /rules."
                    )
                    await update.message.reply_html(welcome_message)

            self.logger.info(f"New members handled in group {chat.id}")
        except Exception as e:
            self.logger.error(f"Error handling new members: {e}")
            await update.message.reply_text(
                "Ha ocurrido un error al dar la bienvenida."
            )

    @group_only
    @admin_only
    @log_command
    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Establece el mensaje de bienvenida personalizado"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Por favor, proporciona un mensaje de bienvenida.\n"
                    "Ejemplo: /welcome ¡Bienvenido al grupo!"
                )
                return

            welcome_message = ' '.join(context.args)
            chat_id = update.effective_chat.id

            # Aquí deberías guardar el mensaje en tu base de datos
            # self.bot_brain.save_welcome_message(chat_id, welcome_message)

            await update.message.reply_text(
                "✅ Mensaje de bienvenida actualizado correctamente."
            )
        except Exception as e:
            self.logger.error(f"Error setting welcome message: {e}")
            await update.message.reply_text(
                "❌ Error al establecer el mensaje de bienvenida."
            )

    @group_only
    @admin_only
    @log_command
    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Establece las reglas del grupo"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Por favor, proporciona las reglas del grupo.\n"
                    "Ejemplo: /rules No spam. Ser respetuoso."
                )
                return

            rules = ' '.join(context.args)
            chat_id = update.effective_chat.id

            # Aquí deberías guardar las reglas en tu base de datos
            # self.bot_brain.save_rules(chat_id, rules)

            await update.message.reply_text(
                "✅ Reglas del grupo actualizadas correctamente."
            )
        except Exception as e:
            self.logger.error(f"Error setting rules: {e}")
            await update.message.reply_text(
                "❌ Error al establecer las reglas del grupo."
            )

    @group_only
    @admin_only
    @log_command
    async def warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Advierte a un usuario"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text(
                    "Por favor, responde al mensaje del usuario que quieres advertir."
                )
                return

            user = update.message.reply_to_message.from_user
            # Aquí deberías implementar la lógica de advertencias
            # warn_count = self.bot_brain.add_warning(user.id, update.effective_chat.id)

            await update.message.reply_html(
                f"⚠️ {user.mention_html()} ha sido advertido."
            )
        except Exception as e:
            self.logger.error(f"Error warning user: {e}")
            await update.message.reply_text(
                "❌ Error al advertir al usuario."
            )

    @group_only
    @admin_only
    @log_command
    async def unwarn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Quita una advertencia a un usuario"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text(
                    "Por favor, responde al mensaje del usuario al que quieres quitar la advertencia."
                )
                return

            user = update.message.reply_to_message.from_user
            # Aquí deberías implementar la lógica de quitar advertencias
            # self.bot_brain.remove_warning(user.id, update.effective_chat.id)

            await update.message.reply_html(
                f"✅ Se ha quitado una advertencia a {user.mention_html()}."
            )
        except Exception as e:
            self.logger.error(f"Error unwarning user: {e}")
            await update.message.reply_text(
                "❌ Error al quitar la advertencia."
            )

    @group_only
    @admin_only
    @log_command
    async def ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Banea a un usuario del grupo"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text(
                    "Por favor, responde al mensaje del usuario que quieres banear."
                )
                return

            user = update.message.reply_to_message.from_user
            chat_id = update.effective_chat.id

            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_html(
                f"🚫 {user.mention_html()} ha sido baneado del grupo."
            )
        except Exception as e:
            self.logger.error(f"Error banning user: {e}")
            await update.message.reply_text(
                "❌ Error al banear al usuario."
            )

    @group_only
    @admin_only
    @log_command
    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Desbanea a un usuario del grupo"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Por favor, proporciona el ID o username del usuario a desbanear."
                )
                return

            user_id = context.args[0]
            chat_id = update.effective_chat.id

            await context.bot.unban_chat_member(chat_id, user_id)
            await update.message.reply_text(
                f"✅ Usuario desbaneado correctamente."
            )
        except Exception as e:
            self.logger.error(f"Error unbanning user: {e}")
            await update.message.reply_text(
                "❌ Error al desbanear al usuario."
            )