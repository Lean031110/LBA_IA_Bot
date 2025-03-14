import sqlite3
from config.config import Config
import os

def setup_database():
    # Asegurarse que el directorio data existe
    os.makedirs('data', exist_ok=True)

    # Leer el esquema SQL
    with open('schema.sql', 'r') as f:
        schema = f.read()

    # Conectar y crear tablas
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.executescript(schema)

        # Insertar usuario admin si no existe
        conn.execute('''
            INSERT OR IGNORE INTO admin_users (id, username, password)
            VALUES (?, ?, ?)
        ''', (
            Config.CREATOR_ID,
            Config.CREATOR_USERNAME.replace('@', ''),
            'tu_contraseña_hasheada'  # Deberías usar una contraseña hasheada real
        ))
        conn.commit()

if __name__ == '__main__':
    setup_database()