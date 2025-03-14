from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from functools import wraps
from datetime import datetime
from config.config import Config_Web
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    try:
        with sqlite3.connect(Config.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username FROM admin_users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                return User(user[0], user[1])
    except Exception as e:
        app.logger.error(f"Error loading user: {e}")
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != Config.CREATOR_ID:
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor complete todos los campos', 'error')
            return redirect(url_for('login'))

        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id, username FROM admin_users WHERE username = ? AND password = ?',
                    (username, password_hash)
                )
                user = cursor.fetchone()

                if user and user[0] == Config.CREATOR_ID:
                    login_user(User(user[0], user[1]))
                    return redirect(url_for('dashboard'))
                else:
                    flash('Credenciales inválidas', 'error')

        except Exception as e:
            app.logger.error(f"Error en login: {e}")
            flash('Error al procesar la solicitud', 'error')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    try:
        with sqlite3.connect(Config.DB_FILE) as conn:
            cursor = conn.cursor()

            # Estadísticas generales
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            total_patterns = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM chat_history')
            total_interactions = cursor.fetchone()[0]

            # Últimas interacciones
            cursor.execute('''
                SELECT user_id, message, timestamp
                FROM chat_history
                ORDER BY timestamp DESC
                LIMIT 10
            ''')
            recent_interactions = cursor.fetchall()

            return render_template(
                'dashboard.html',
                total_patterns=total_patterns,
                total_interactions=total_interactions,
                recent_interactions=recent_interactions
            )

    except Exception as e:
        app.logger.error(f"Error en dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/knowledge')
@login_required
@admin_required
def knowledge():
    try:
        with sqlite3.connect(Config.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT pattern, response, confidence FROM knowledge')
            patterns = cursor.fetchall()
            return render_template('knowledge.html', patterns=patterns)
    except Exception as e:
        app.logger.error(f"Error al cargar knowledge: {e}")
        flash('Error al cargar la base de conocimiento', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/add_pattern', methods=['POST'])
@login_required
@admin_required
def add_pattern():
    try:
        pattern = request.form.get('pattern')
        response = request.form.get('response')
        confidence = float(request.form.get('confidence', 0.8))

        if not pattern or not response:
            return jsonify({'success': False, 'error': 'Datos incompletos'})

        with sqlite3.connect(Config.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO knowledge (pattern, response, confidence) VALUES (?, ?, ?)',
                (pattern, response, confidence)
            )
            conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error al añadir patrón: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
@login_required
@admin_required
def get_stats():
    try:
        with sqlite3.connect(Config.DB_FILE) as conn:
            cursor = conn.cursor()

            # Estadísticas generales
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            total_patterns = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM chat_history')
            total_interactions = cursor.fetchone()[0]

            # Actividad por hora
            cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM chat_history
                GROUP BY hour
                ORDER BY hour
            ''')
            hourly_activity = cursor.fetchall()

            return jsonify({
                'success': True,
                'stats': {
                    'total_patterns': total_patterns,
                    'total_interactions': total_interactions,
                    'hourly_activity': dict(hourly_activity)
                }
            })

    except Exception as e:
        app.logger.error(f"Error al obtener estadísticas: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False)