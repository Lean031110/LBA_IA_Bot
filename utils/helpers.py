import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

def clean_text(text: str) -> str:
    """Limpia y normaliza un texto"""
    # Convertir a minúsculas
    text = text.lower()

    # Eliminar caracteres especiales y espacios extras
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def format_time(seconds: int) -> str:
    """Formatea segundos en un string legible"""
    if seconds < 60:
        return f"{seconds} segundos"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutos"
    else:
        hours = seconds // 3600
        return f"{hours} horas"

def parse_time(text: str) -> Optional[int]:
    """Convierte texto de tiempo en segundos"""
    time_map = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    match = re.match(r'^(\d+)([smhd])$', text.lower())
    if match:
        value, unit = match.groups()
        return int(value) * time_map[unit]
    return None

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Carga un archivo JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}

def save_json_file(filepath: str, data: Dict[str, Any]) -> bool:
    """Guarda datos en un archivo JSON"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

def get_time_diff(date: datetime) -> str:
    """Obtiene la diferencia de tiempo en formato legible"""
    now = datetime.now()
    diff = now - date

    if diff.days > 0:
        return f"hace {diff.days} días"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"hace {hours} horas"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"hace {minutes} minutos"
    else:
        return f"hace {diff.seconds} segundos"