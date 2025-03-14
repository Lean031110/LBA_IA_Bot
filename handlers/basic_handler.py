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
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    @log_command
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /help"""
        keyboard = self.keyboards.get_help_menu()
        await update.message.reply_text(
            Config.MESSAGES['help'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
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

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja las respuestas a los botones inline"""
        query = update.callback_query
        data = query.data

        try:
            # Manejar diferentes tipos de callbacks
            if data.startswith('help_'):
                await self.handle_help_callback(query)
            elif data.startswith('info_'):
                await self.handle_info_callback(query)
            elif data.startswith('main_'):
                await self.handle_main_menu_callback(query)
            else:
                await query.answer("⚠️ Opción no válida")

        except Exception as e:
            await query.answer("❌ Error al procesar la solicitud")
            print(f"Error en handle_callback: {e}")

    async def handle_help_callback(self, query) -> None:
        """Maneja callbacks del menú de ayuda"""
        data = query.data.split('_')[1]

        help_texts = {
            'commands': """📝 *Comandos Disponibles:*
• /start - Inicia el bot
• /help - Muestra este mensaje
• /info - Información sobre el bot
• /search - Realiza una búsqueda
• /wiki - Busca en Wikipedia""",

            'admin': """👑 *Comandos de Administración:*
• /config - Configura el bot
• /stats - Muestra estadísticas
• /train - Entrena al bot
• /backup - Realiza una copia de seguridad""",

            'group': """👥 *Comandos de Grupo:*
• /welcome - Configura mensaje de bienvenida
• /rules - Establece reglas del grupo
• /warn - Advierte a un usuario
• /unwarn - Quita advertencia
• /ban - Banea usuario
• /unban - Desbanea usuario"""
        }

        if data in help_texts:
            keyboard = self.keyboards.get_help_menu()
            await query.message.edit_text(
                help_texts[data],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

        await query.answer()

    async def handle_info_callback(self, query) -> None:
        """Maneja callbacks del menú de información"""
        data = query.data.split('_')[1]

        info_texts = {
            'about': """ℹ️ *Sobre el Bot*
Este bot fue creado para ayudar en la gestión de grupos y proporcionar funcionalidades de IA.""",

            'stats': """📊 *Estadísticas*
• Usuarios: {users}
• Grupos: {groups}
• Mensajes: {messages}""",

            'help': """💡 *Ayuda Rápida*
Usa /help para ver todos los comandos disponibles."""
        }

        if data in info_texts:
            keyboard = self.keyboards.get_info_menu()
            await query.message.edit_text(
                info_texts[data].format(
                    users=0,  # TODO: Implementar contadores reales
                    groups=0,
                    messages=0
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

        await query.answer()

    async def handle_main_menu_callback(self, query) -> None:
        """Maneja callbacks del menú principal"""
        data = query.data.split('_')[1]

        menu_actions = {
            'help': self.help,
            'info': self.info,
            'credit': self.credit
        }

        if data in menu_actions:
            # Crear un Update falso para poder reutilizar los métodos existentes
            fake_update = Update(
                update_id=0,
                message=query.message
            )
            await menu_actions[data](fake_update, None)

        await query.answer()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja mensajes normales"""
        if not update.message or not update.message.text:
            return

        response = await self.bot_brain.process_message(
            update.message.text,
            update.effective_user.id
        )

        if response:
            await update.message.reply_text(
                response,
                parse_mode='Markdown'
            )