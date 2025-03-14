"""
Archivo de configuración para variables que pueden cambiar durante la ejecución
"""
from typing import Dict, Any

class Settings:
    """Clase para manejar configuraciones dinámicas"""

    _instance = None
    _settings: Dict[str, Any] = {
        'maintenance_mode': False,
        'debug_mode': False,
        'allowed_groups': set(),
        'banned_users': set(),
        'disabled_commands': set(),
        'custom_responses': {},
        'group_settings': {},
        'cached_data': {}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Obtener un valor de configuración"""
        return cls._settings.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Establecer un valor de configuración"""
        cls._settings[key] = value

    @classmethod
    def toggle(cls, key: str) -> bool:
        """Alternar un valor booleano"""
        current = cls._settings.get(key, False)
        cls._settings[key] = not current
        return not current

    @classmethod
    def add_to_set(cls, key: str, value: Any) -> None:
        """Añadir un valor a un conjunto"""
        if key not in cls._settings:
            cls._settings[key] = set()
        cls._settings[key].add(value)

    @classmethod
    def remove_from_set(cls, key: str, value: Any) -> None:
        """Eliminar un valor de un conjunto"""
        if key in cls._settings and isinstance(cls._settings[key], set):
            cls._settings[key].discard(value)

    @classmethod
    def update_group_settings(cls, group_id: int, settings: Dict[str, Any]) -> None:
        """Actualizar configuración de un grupo"""
        if 'group_settings' not in cls._settings:
            cls._settings['group_settings'] = {}

        if group_id not in cls._settings['group_settings']:
            cls._settings['group_settings'][group_id] = {}

        cls._settings['group_settings'][group_id].update(settings)

    @classmethod
    def get_group_settings(cls, group_id: int) -> Dict[str, Any]:
        """Obtener configuración de un grupo"""
        return cls._settings.get('group_settings', {}).get(group_id, {})

    @classmethod
    def reset(cls) -> None:
        """Resetear todas las configuraciones a valores predeterminados"""
        cls._settings = {
            'maintenance_mode': False,
            'debug_mode': False,
            'allowed_groups': set(),
            'banned_users': set(),
            'disabled_commands': set(),
            'custom_responses': {},
            'group_settings': {},
            'cached_data': {}
        }