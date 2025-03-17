import os
import logging
import secrets
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define User model at module level
class User(UserMixin, db.Model):
    __tablename__ = 'web_users'  # Cambiado para evitar conflictos
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def create_app():
    """Crea y configura la aplicación Flask"""
    logger.info("Iniciando creación de la aplicación Flask...")
    app = Flask(__name__)

    try:
        # Configuración
        # Generar SESSION_SECRET si no existe
        if not os.environ.get('SESSION_SECRET'):
            os.environ['SESSION_SECRET'] = secrets.token_hex(32)
            logger.info("SESSION_SECRET generado automáticamente")

        app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')
        
        # Asegurarse de que la URL de la base de datos esté disponible
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            from dotenv import load_dotenv
            load_dotenv()
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL no está definida en las variables de entorno")
                database_url = "sqlite:///fallback.db"
                logger.warning(f"Usando base de datos de respaldo: {database_url}")
        
        # Mostrar información de conexión (sin contraseñas)
        safe_db_url = database_url
        if '@' in safe_db_url and ':' in safe_db_url.split('@')[0]:
            # Ocultar contraseña en los logs
            parts = safe_db_url.split('@')
            credentials = parts[0].split(':')
            if len(credentials) > 2:  # postgresql://user:pass@host
                masked_url = f"{credentials[0]}:{credentials[1]}:****@{parts[1]}"
            else:  # user:pass@host
                masked_url = f"{credentials[0]}:****@{parts[1]}"
            logger.info(f"Usando conexión a base de datos: {masked_url}")
        else:
            logger.info(f"Usando conexión a base de datos: {safe_db_url}")
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_recycle': 60,        # Reducido para evitar conexiones obsoletas
            'pool_pre_ping': True,     # Verifica conexión antes de usar
            'connect_args': {
                'connect_timeout': 10,  # Timeout de conexión en segundos
                'keepalives': 1,        # Mantener conexión viva
                'keepalives_idle': 30,  # Tiempo de inactividad antes de enviar keepalive
                'keepalives_interval': 10,  # Intervalo entre keepalives
                'keepalives_count': 5   # Número de keepalives fallidos antes de cerrar
            }
        }

        logger.info("Configuración de Flask cargada correctamente")

        # Initialize extensions
        db.init_app(app)
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'login'

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Create tables
        with app.app_context():
            db.create_all()
            # Create admin user if not exists
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', is_admin=True)
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
                db.session.add(admin)
                db.session.commit()
                logger.info("Usuario admin creado correctamente")

        # Import routes
        from web.routes import register_routes
        register_routes(app)

        logger.info("Aplicación Flask creada correctamente")
        return app

    except Exception as e:
        logger.error(f"Error al crear la aplicación Flask: {e}")
        raise

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)