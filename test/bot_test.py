import pytest
from core.bot_brain import BotBrain
from unittest.mock import patch

# Datos de prueba
test_data = [
    ("Hola", "¡Hola! ¿Cómo puedo ayudarte?"),
    ("¿Cuál es tu nombre?", "Soy un bot con IA. ¿Cómo puedo ayudarte?"),
    ("¿Qué puedes hacer?", "Puedo ayudarte con varias tareas. Pregúntame algo."),
]

@pytest.fixture
def bot_brain():
    """Fixture para inicializar la instancia de BotBrain usando una base de datos en memoria"""
    with patch('core.bot_brain.Config.DB_FILE', ':memory:'):
        return BotBrain()

@pytest.mark.asyncio
async def test_bot_brain_response(bot_brain):
    """Prueba para verificar las respuestas del bot"""
    for question, expected_response in test_data:
        response = await bot_brain.get_response(question)
        assert response == expected_response, f"Para '{question}', se esperaba '{expected_response}' pero se obtuvo '{response}'"

@pytest.mark.asyncio
async def test_bot_brain_confidence(bot_brain):
    """Prueba para verificar el nivel de confianza del bot"""
    for question, _ in test_data:
        confidence = await bot_brain.get_confidence(question)
        assert confidence >= 0.5, f"El nivel de confianza para '{question}' es muy bajo: {confidence}"
