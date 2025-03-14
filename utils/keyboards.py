from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class BaseKeyboards:
    @staticmethod
    def build_menu(
        buttons: List[InlineKeyboardButton],
        n_cols: int = 1,
        header_buttons: Optional[List[InlineKeyboardButton]] = None,
        footer_buttons: Optional[List[InlineKeyboardButton]] = None
    ) -> List[List[InlineKeyboardButton]]:
        """Construye un menú de botones en columnas"""
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu

    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Teclado principal del bot"""
        buttons = [
            [
                InlineKeyboardButton("🔍 Buscar", callback_data="search"),
                InlineKeyboardButton("ℹ️ Ayuda", callback_data="help")
            ],
            [
                InlineKeyboardButton("📊 Estadísticas", callback_data="stats"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="config")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_help_menu() -> InlineKeyboardMarkup:
        """Teclado del menú de ayuda"""
        buttons = [
            [
                InlineKeyboardButton("📖 Guía de uso", callback_data="guide"),
                InlineKeyboardButton("❓ FAQ", callback_data="faq")
            ],
            [
                InlineKeyboardButton("📱 Comandos", callback_data="commands"),
                InlineKeyboardButton("💡 Tips", callback_data="tips")
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_info_menu() -> InlineKeyboardMarkup:
        """Teclado del menú de información"""
        buttons = [
            [
                InlineKeyboardButton("📊 Estado", callback_data="status"),
                InlineKeyboardButton("📝 Changelog", callback_data="changelog")
            ],
            [
                InlineKeyboardButton("👥 Créditos", callback_data="credits"),
                InlineKeyboardButton("🌐 Website", url="https://github.com/Lean031110/LBA_IA_Bot")
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_config_menu() -> InlineKeyboardMarkup:
        """Teclado de configuración"""
        buttons = [
            [
                InlineKeyboardButton("🤖 IA", callback_data="config_ai"),
                InlineKeyboardButton("👥 Grupos", callback_data="config_groups")
            ],
            [
                InlineKeyboardButton("🔒 Privacidad", callback_data="config_privacy"),
                InlineKeyboardButton("📝 Comandos", callback_data="config_commands")
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_credit_menu() -> InlineKeyboardMarkup:
        """Teclado del menú de créditos"""
        buttons = [
            [
                InlineKeyboardButton("👨‍💻 GitHub", url="https://github.com/Lean031110"),
                InlineKeyboardButton("📱 Telegram", url="https://t.me/Lean031110")
            ],
            [
                InlineKeyboardButton("💝 Donar", callback_data="donate"),
                InlineKeyboardButton("⭐ Calificar", callback_data="rate")
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_confirmation_menu(action: str) -> InlineKeyboardMarkup:
        """Teclado de confirmación"""
        buttons = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_pagination_menu(
        current_page: int,
        total_pages: int,
        base_callback: str
    ) -> InlineKeyboardMarkup:
        """Teclado de paginación"""
        buttons = []

        # Botones de navegación
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️", callback_data=f"{base_callback}_page_{current_page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        )
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("➡️", callback_data=f"{base_callback}_page_{current_page+1}")
            )
        buttons.append(nav_buttons)

        # Botón de volver
        buttons.append([InlineKeyboardButton("🔙 Volver", callback_data="main_menu")])

        return InlineKeyboardMarkup(buttons)