import sqlite3
from datetime import datetime
import logging
from config.config import Config
from utils.helpers import clean_text
from typing import Dict, List, Tuple, Optional, Any
import json
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class BotBrain:
    """Clase principal para el manejo de la IA y datos del bot"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vectorizer = TfidfVectorizer()
        self.knowledge_base = {}
        self.conversation_history = {}
        self._setup_database()
        self.load_knowledge_base()

    def _setup_database(self) -> None:
        """Configura la base de datos"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()

                # Tabla de usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_seen TIMESTAMP,
                        last_active TIMESTAMP,
                        interaction_count INTEGER DEFAULT 0,
                        is_banned BOOLEAN DEFAULT 0
                    )
                ''')

                # Tabla de conocimiento
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern TEXT UNIQUE,
                        response TEXT,
                        confidence REAL DEFAULT 0.8,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        used_count INTEGER DEFAULT 0
                    )
                ''')

                # Tabla de historial de chat
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        message TEXT,
                        response TEXT,
                        confidence REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')

                # Tabla de grupos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS groups (
                        group_id INTEGER PRIMARY KEY,
                        title TEXT,
                        join_date TIMESTAMP,
                        member_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            raise

    def load_knowledge_base(self) -> None:
        """Carga la base de conocimiento desde la base de datos"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT pattern, response, confidence FROM knowledge')
                rows = cursor.fetchall()

                for pattern, response, confidence in rows:
                    self.knowledge_base[pattern] = {
                        'response': response,
                        'confidence': confidence,
                        'vector': None
                    }

        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            raise

    async def process_message(self, text: str, user_id: int) -> Tuple[str, float]:
        """Procesa un mensaje y genera una respuesta"""
        try:
            # Limpiar y preparar el texto
            clean_input = clean_text(text)

            # Buscar mejor coincidencia
            response, confidence = await self._find_best_match(clean_input)

            # Registrar la interacción
            await self._log_interaction(user_id, text, response, confidence)

            # Actualizar estadísticas de uso
            await self._update_usage_stats(user_id)

            return response, confidence

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return "Lo siento, ha ocurrido un error.", 0.0

    async def _find_best_match(self, text: str) -> Tuple[str, float]:
        """Encuentra la mejor coincidencia para un texto dado"""
        try:
            if not self.knowledge_base:
                return "Aún estoy aprendiendo.", 0.0

            best_match = None
            best_confidence = 0.0

            # Vectorizar texto de entrada
            input_vector = self.vectorizer.fit_transform([text])

            for pattern, data in self.knowledge_base.items():
                # Calcular vector si no existe
                if data['vector'] is None:
                    data['vector'] = self.vectorizer.transform([pattern])

                # Calcular similitud
                similarity = cosine_similarity(input_vector, data['vector'])[0][0]
                confidence = similarity * data['confidence']

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = data['response']

            if best_confidence < Config.MIN_CONFIDENCE:
                return "No estoy seguro de cómo responder a eso.", best_confidence

            return best_match, best_confidence

        except Exception as e:
            self.logger.error(f"Error finding best match: {e}")
            raise

    async def learn(self, pattern: str, response: str, confidence: float = 0.8) -> bool:
        """Aprende un nuevo patrón de respuesta"""
        try:
            pattern = clean_text(pattern)
            if not pattern or not response:
                return False

            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO knowledge (pattern, response, confidence)
                    VALUES (?, ?, ?)
                ''', (pattern, response, confidence))
                conn.commit()

            self.knowledge_base[pattern] = {
                'response': response,
                'confidence': confidence,
                'vector': None
            }

            return True

        except Exception as e:
            self.logger.error(f"Error learning pattern: {e}")
            return False

    async def _log_interaction(self, user_id: int, message: str, response: str, confidence: float) -> None:
        """Registra una interacción en la base de datos"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_history (user_id, message, response, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, message, response, confidence))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")

    async def _update_usage_stats(self, user_id: int) -> None:
        """Actualiza estadísticas de uso del usuario"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users
                    SET interaction_count = interaction_count + 1,
                        last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating usage stats: {e}")

    async def register_user(self, user_id: int, username: str) -> None:
        """Registra un nuevo usuario"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, username, first_seen, last_active)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, username))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error registering user: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas básicas del bot"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()

                # Total de usuarios
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]

                # Total de mensajes
                cursor.execute('SELECT COUNT(*) FROM chat_history')
                total_messages = cursor.fetchone()[0]

                # Patrones aprendidos
                cursor.execute('SELECT COUNT(*) FROM knowledge')
                total_patterns = cursor.fetchone()[0]

                # Precisión promedio
                cursor.execute('SELECT AVG(confidence) FROM chat_history')
                accuracy = cursor.fetchone()[0] or 0.0

                return {
                    'total_users': total_users,
                    'total_messages': total_messages,
                    'total_patterns': total_patterns,
                    'accuracy': round(accuracy * 100, 2)
                }

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {
                'total_users': 0,
                'total_messages': 0,
                'total_patterns': 0,
                'accuracy': 0.0
            }

    async def create_backup(self) -> Optional[str]:
        """Crea un respaldo de la base de datos"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{Config.BACKUP_DIR}/backup_{timestamp}.json"

            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()

                # Obtener datos
                data = {
                    'knowledge': [],
                    'users': [],
                    'chat_history': [],
                    'groups': []
                }

                # Exportar conocimiento
                cursor.execute('SELECT * FROM knowledge')
                for row in cursor.fetchall():
                    data['knowledge'].append({
                        'id': row[0],
                        'pattern': row[1],
                        'response': row[2],
                        'confidence': row[3],
                        'created_at': row[4],
                        'used_count': row[5]
                    })

                # Exportar usuarios
                cursor.execute('SELECT * FROM users')
                for row in cursor.fetchall():
                    data['users'].append({
                        'user_id': row[0],
                        'username': row[1],
                        'first_seen': row[2],
                        'last_active': row[3],
                        'interaction_count': row[4],
                        'is_banned': row[5]
                    })

                # Guardar respaldo
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                return backup_file

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    async def restore_backup(self, backup_file: str) -> bool:
        """Restaura un respaldo de la base de datos"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()

                # Restaurar conocimiento
                cursor.executemany('''
                    INSERT OR REPLACE INTO knowledge
                    (id, pattern, response, confidence, created_at, used_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [(k['id'], k['pattern'], k['response'], k['confidence'],
                      k['created_at'], k['used_count']) for k in data['knowledge']])

                # Restaurar usuarios
                cursor.executemany('''
                    INSERT OR REPLACE INTO users
                    (user_id, username, first_seen, last_active, interaction_count, is_banned)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [(u['user_id'], u['username'], u['first_seen'],
                      u['last_active'], u['interaction_count'], u['is_banned'])
                     for u in data['users']])

                conn.commit()

            # Recargar base de conocimiento
            self.load_knowledge_base()
            return True

        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False