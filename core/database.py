import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from config.config import Config
import os
import json

class Database:
    """Manejador de base de datos del bot"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_file = Config.DB_FILE
        self._ensure_directories()
        self._setup_database()

    def _ensure_directories(self) -> None:
        """Asegura que existan los directorios necesarios"""
        directories = [
            os.path.dirname(self.db_file),
            Config.BACKUP_DIR,
            Config.LOG_DIR
        ]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def _setup_database(self) -> None:
        """Configura la estructura inicial de la base de datos"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Tabla de usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_seen TIMESTAMP,
                        last_active TIMESTAMP,
                        interaction_count INTEGER DEFAULT 0,
                        is_banned BOOLEAN DEFAULT 0,
                        settings TEXT DEFAULT '{}'
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
                        used_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP
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
                        is_active BOOLEAN DEFAULT 1,
                        settings TEXT DEFAULT '{}'
                    )
                ''')

                # Tabla de moderación
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS moderation (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        group_id INTEGER,
                        action_type TEXT,
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (group_id) REFERENCES groups (group_id)
                    )
                ''')

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_file)

    async def execute_query(self, query: str, params: tuple = ()) -> Optional[List[tuple]]:
        """Ejecuta una consulta SQL"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if query.lower().startswith('select'):
                    return cursor.fetchall()

                conn.commit()
                return None

        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise

    async def execute_many(self, query: str, params: List[tuple]) -> None:
        """Ejecuta múltiples consultas SQL"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params)
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error executing many queries: {e}")
            raise

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene información de un usuario"""
        query = 'SELECT * FROM users WHERE user_id = ?'
        result = await self.execute_query(query, (user_id,))

        if result and result[0]:
            return {
                'user_id': result[0][0],
                'username': result[0][1],
                'first_seen': result[0][2],
                'last_active': result[0][3],
                'interaction_count': result[0][4],
                'is_banned': bool(result[0][5]),
                'settings': json.loads(result[0][6])
            }
        return None

    async def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Actualiza información de un usuario"""
        if 'settings' in data and isinstance(data['settings'], dict):
            data['settings'] = json.dumps(data['settings'])

        fields = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f'UPDATE users SET {fields} WHERE user_id = ?'
        params = tuple(data.values()) + (user_id,)
        await self.execute_query(query, params)

    async def create_user(self, user_id: int, username: str) -> None:
        """Crea un nuevo usuario"""
        query = '''
            INSERT OR IGNORE INTO users (user_id, username, first_seen, last_active)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        '''
        await self.execute_query(query, (user_id, username))

    async def add_chat_history(self, user_id: int, message: str,
                             response: str, confidence: float) -> None:
        """Añade una entrada al historial de chat"""
        query = '''
            INSERT INTO chat_history (user_id, message, response, confidence)
            VALUES (?, ?, ?, ?)
        '''
        await self.execute_query(query, (user_id, message, response, confidence))

    async def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el historial de chat de un usuario"""
        query = '''
            SELECT message, response, confidence, timestamp
            FROM chat_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        results = await self.execute_query(query, (user_id, limit))

        return [
            {
                'message': row[0],
                'response': row[1],
                'confidence': row[2],
                'timestamp': row[3]
            }
            for row in (results or [])
        ]

    async def add_knowledge(self, pattern: str, response: str, confidence: float) -> None:
        """Añade una nueva entrada a la base de conocimiento"""
        query = '''
            INSERT OR REPLACE INTO knowledge (pattern, response, confidence)
            VALUES (?, ?, ?)
        '''
        await self.execute_query(query, (pattern, response, confidence))

    async def get_knowledge(self, pattern: str = None) -> List[Dict[str, Any]]:
        """Obtiene entradas de la base de conocimiento"""
        if pattern:
            query = 'SELECT * FROM knowledge WHERE pattern = ?'
            results = await self.execute_query(query, (pattern,))
        else:
            query = 'SELECT * FROM knowledge'
            results = await self.execute_query(query)

        return [
            {
                'id': row[0],
                'pattern': row[1],
                'response': row[2],
                'confidence': row[3],
                'created_at': row[4],
                'used_count': row[5],
                'last_used': row[6]
            }
            for row in (results or [])
        ]

    async def update_knowledge(self, pattern: str, data: Dict[str, Any]) -> None:
        """Actualiza una entrada de la base de conocimiento"""
        fields = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f'UPDATE knowledge SET {fields}, last_used = CURRENT_TIMESTAMP WHERE pattern = ?'
        params = tuple(data.values()) + (pattern,)
        await self.execute_query(query, params)

    async def delete_knowledge(self, pattern: str) -> None:
        """Elimina una entrada de la base de conocimiento"""
        query = 'DELETE FROM knowledge WHERE pattern = ?'
        await self.execute_query(query, (pattern,))

    async def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene información de un grupo"""
        query = 'SELECT * FROM groups WHERE group_id = ?'
        result = await self.execute_query(query, (group_id,))

        if result and result[0]:
            return {
                'group_id': result[0][0],
                'title': result[0][1],
                'join_date': result[0][2],
                'member_count': result[0][3],
                'is_active': bool(result[0][4]),
                'settings': json.loads(result[0][5])
            }
        return None

    async def update_group(self, group_id: int, data: Dict[str, Any]) -> None:
        """Actualiza información de un grupo"""
        if 'settings' in data and isinstance(data['settings'], dict):
            data['settings'] = json.dumps(data['settings'])

        fields = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f'UPDATE groups SET {fields} WHERE group_id = ?'
        params = tuple(data.values()) + (group_id,)
        await self.execute_query(query, params)

    async def add_moderation_action(self, user_id: int, group_id: int,
                                  action_type: str, reason: str,
                                  expires_at: Optional[datetime] = None) -> None:
        """Añade una acción de moderación"""
        query = '''
            INSERT INTO moderation (user_id, group_id, action_type, reason, expires_at)
            VALUES (?, ?, ?, ?, ?)
        '''
        await self.execute_query(query, (user_id, group_id, action_type, reason, expires_at))

    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales"""
        stats = {}

        # Usuarios
        user_stats = await self.execute_query('''
            SELECT
                COUNT(*) as total_users,
                COUNT(CASE WHEN last_active > datetime('now', '-24 hours') THEN 1 END) as active_today,
                COUNT(CASE WHEN first_seen > datetime('now', '-24 hours') THEN 1 END) as new_today
            FROM users
        ''')

        if user_stats and user_stats[0]:
            stats['users'] = {
                'total': user_stats[0][0],
                'active_today': user_stats[0][1],
                'new_today': user_stats[0][2]
            }

        # Mensajes
        message_stats = await self.execute_query('''
            SELECT
                COUNT(*) as total_messages,
                COUNT(CASE WHEN timestamp > datetime('now', '-24 hours') THEN 1 END) as messages_today,
                AVG(confidence) as avg_confidence
            FROM chat_history
        ''')

        if message_stats and message_stats[0]:
            stats['messages'] = {
                'total': message_stats[0][0],
                'today': message_stats[0][1],
                'avg_confidence': round(message_stats[0][2] * 100, 2) if message_stats[0][2] else 0
            }

        # Base de conocimiento
        knowledge_stats = await self.execute_query('''
            SELECT COUNT(*) as total_patterns
            FROM knowledge
        ''')

        if knowledge_stats and knowledge_stats[0]:
            stats['knowledge'] = {
                'total_patterns': knowledge_stats[0][0]
            }

        return stats

    async def cleanup_old_data(self, days: int = 30) -> None:
        """Limpia datos antiguos de la base de datos"""
        try:
            queries = [
                '''DELETE FROM chat_history
                   WHERE timestamp < datetime('now', '-? days')''',
                '''DELETE FROM users
                   WHERE last_active < datetime('now', '-? days')
                   AND interaction_count = 0''',
                '''DELETE FROM moderation
                   WHERE timestamp < datetime('now', '-? days')'''
            ]

            for query in queries:
                await self.execute_query(query, (days,))

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")

    async def backup_database(self) -> Tuple[bool, str]:
        """Crea una copia de seguridad de la base de datos"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{Config.BACKUP_DIR}/backup_{timestamp}.db"

        try:
            with self._get_connection() as conn:
                backup = sqlite3.connect(backup_path)
                conn.backup(backup)
                backup.close()
            return True, backup_path
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False, str(e)

    async def restore_backup(self, backup_path: str) -> bool:
        """Restaura una copia de seguridad"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError("Backup file not found")

            # Crear respaldo temporal de la base actual
            current_backup = await self.backup_database()

            # Restaurar desde el archivo de respaldo
            with sqlite3.connect(backup_path) as backup:
                with self._get_connection() as conn:
                    backup.backup(conn)

            return True

        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False