from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.config import Config
from utils.keyboards import BaseKeyboards
from utils.decorators import log_command

class BasicHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain
        self.keyboards = BaseKeyboards()

    @log_command
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /start"""
        keyboard = self.keyboards.get_main_menu()
        await update.message.reply_text(
            Config.MESSAGES['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @log_command
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /help"""
        keyboard = self.keyboards.get_help_menu()
        await update.message.reply_text(
            Config.MESSAGES['help'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @log_command
    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /info"""
        info_text = """🤖 *LBA IA Bot* - Versión 1.0

📋 Características:
• IA Integrada
• Moderación Automática
• Búsqueda Inteligente
• Sistema de Aprendizaje

💡 Creado por @Lean031110
🔧 Mantenimiento activo
        """
        keyboard = self.keyboards.get_info_menu()
        await update.message.reply_text(
            info_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @log_command
    async def credit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /credit"""
        credit_text = """👨‍💻 *Desarrollado por:*
@Lean031110

🌟 *Agradecimientos especiales:*
• Comunidad de Telegram
• Contribuidores del proyecto

📝 *Licencia:*
Este bot está bajo licencia MIT.

🔗 *Enlaces útiles:*
• [GitHub](https://github.com/Lean031110)
• [Documentación](https://your-docs-url.com)
"""
        keyboard = self.keyboards.get_credit_menu()
        await update.message.reply_text(
            credit_text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )