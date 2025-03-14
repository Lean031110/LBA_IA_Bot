from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
from utils.decorators import admin_only, log_command

class AdminHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain

    @admin_only
    @log_command
    async def config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /config (solo admin)"""
        keyboard = self.keyboards.get_config_menu()
        config_text = """⚙️ *Panel de Configuración*

🔐 *Opciones disponibles:*
• Ajustes de IA
• Configuración de moderación
• Gestión de permisos
• Respaldo de datos

Usa los botones para navegar.
        """
        await update.message.reply_text(
            config_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    @admin_only
    @log_command
    async def train(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /train (solo admin)"""
        args = context.args
        if not args or len(args) < 2:
            await update.message.reply_text(
                "❌ Uso correcto: /train 'patrón' 'respuesta'\n"
                "Ejemplo: /train 'hola bot' 'Hola, ¿en qué puedo ayudarte?'"
            )
            return

        pattern = args[0]
        response = ' '.join(args[1:])

        if self.bot_brain.learn(pattern, response):
            await update.message.reply_text(
                "✅ ¡Aprendizaje exitoso!\n"
                f"Patrón: {pattern}\n"
                f"Respuesta: {response}"
            )
        else:
            await update.message.reply_text(
                "❌ Error al intentar aprender el nuevo patrón."
            )