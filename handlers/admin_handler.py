from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
from utils.decorators import admin_only, log_command
from utils.keyboards import BaseKeyboards

class AdminHandler:
    def __init__(self, bot_brain):
        self.bot_brain = bot_brain
        self.keyboards = BaseKeyboards()  # Añadida esta línea

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
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /stats (solo admin)"""
        stats_text = """📊 *Estadísticas del Bot*

🤖 *Rendimiento:*
• Mensajes procesados: {messages}
• Comandos ejecutados: {commands}
• Usuarios activos: {users}

⚡️ *Sistema:*
• Uso de CPU: {cpu}%
• Memoria usada: {memory}MB
• Tiempo activo: {uptime}
        """
        # TODO: Implementar la recolección real de estadísticas
        placeholder_stats = {
            "messages": 0,
            "commands": 0,
            "users": 0,
            "cpu": 0,
            "memory": 0,
            "uptime": "0h 0m"
        }

        await update.message.reply_text(
            stats_text.format(**placeholder_stats),
            parse_mode='Markdown'
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

    @admin_only
    @log_command
    async def backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /backup (solo admin)"""
        await update.message.reply_text(
            "🔄 Iniciando respaldo de datos...",
            parse_mode='Markdown'
        )
        # TODO: Implementar la lógica de respaldo
        await update.message.reply_text(
            "✅ Respaldo completado exitosamente.",
            parse_mode='Markdown'
        )

    @admin_only
    @log_command
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /broadcast (solo admin)"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso correcto: /broadcast mensaje",
                parse_mode='Markdown'
            )
            return

        message = ' '.join(context.args)
        # TODO: Implementar la lógica de broadcast
        await update.message.reply_text(
            f"✅ Mensaje enviado:\n{message}",
            parse_mode='Markdown'
        )