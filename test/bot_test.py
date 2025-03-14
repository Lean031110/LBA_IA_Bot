import pytest
from unittest.mock import patch
import sqlite3
from core.bot import Bot
from core.bot_brain import BotBrain
from web.app import create_app
from aiohttp.test_utils import TestClient, TestServer, loop_context

# Datos de prueba
test_data_bot = [
    ("Hola", "¡Hola! ¿Cómo puedo ayudarte?"),
    ("¿Cuál es tu nombre?", "Soy un bot con IA. ¿Cómo puedo ayudarte?"),
    ("¿Qué puedes hacer?", "Puedo ayudarte con varias tareas. Pregúntame algo."),
]

test_data_ia = [
    ("¿Cuál es la capital de Francia?", "La capital de Francia es París."),
    ("¿Quién escribió 'Don Quijote'?", "Miguel de Cervantes escribió 'Don Quijote'."),
]

@pytest.fixture
def bot_brain():
    """Fixture para inicializar la instancia de BotBrain usando una base de datos en memoria"""
    with patch('core.bot_brain.Config.DB_FILE', ':memory:'):
        # Crear instancia de BotBrain
        bot_brain = BotBrain()

        # Crear la tabla y agregar datos de prueba
        with sqlite3.connect(':memory:') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE knowledge (
                    pattern TEXT,
                    response TEXT,
                    confidence REAL
                )
            """)
            cursor.executemany("""
                INSERT INTO knowledge (pattern, response, confidence) VALUES (?, ?, ?)
            """, [
                ("Hola", "¡Hola! ¿Cómo puedo ayudarte?", 1.0),
                ("¿Cuál es tu nombre?", "Soy un bot con IA. ¿Cómo puedo ayudarte?", 1.0),
                ("¿Qué puedes hacer?", "Puedo ayudarte con varias tareas. Pregúntame algo.", 1.0),
                ("¿Cuál es la capital de Francia?", "La capital de Francia es París.", 1.0),
                ("¿Quién escribió 'Don Quijote'?", "Miguel de Cervantes escribió 'Don Quijote'.", 1.0)
            ])
            conn.commit()

        # Parchea el método `load_knowledge_base` para usar la base de datos en memoria
        bot_brain.load_knowledge_base = lambda: None

        return bot_brain

@pytest.fixture
def bot():
    """Fixture para inicializar el Bot"""
    return Bot()

@pytest.mark.asyncio
async def test_bot_responses(bot_brain):
    """Prueba para verificar las respuestas del bot"""
    for question, expected_response in test_data_bot:
        response = await bot_brain.get_response(question)
        assert response == expected_response, f"Para '{question}', se esperaba '{expected_response}' pero se obtuvo '{response}'"

@pytest.mark.asyncio
async def test_ia_responses(bot_brain):
    """Prueba para verificar las respuestas de la IA"""
    for question, expected_response in test_data_ia:
        response = await bot_brain.get_response(question)
        assert response == expected_response, f"Para '{question}', se esperaba '{expected_response}' pero se obtuvo '{response}'"

@pytest.fixture
async def web_client(aiohttp_client, event_loop):
    """Fixture para inicializar el cliente web"""
    app = create_app()
    client = await aiohttp_client(app)
    return client

@pytest.mark.asyncio
async def test_web_application(web_client):
    """Prueba para verificar la aplicación web"""
    resp = await web_client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert "Bienvenido a la aplicación web del bot" in text
