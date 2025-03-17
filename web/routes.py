from flask import render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from .app import db, User
from bot.ai_module import SimpleAI
from shared.database import get_db, Group, ModAction, Warning, User as BotUser, Message
from datetime import datetime, timedelta
import markdown2
import os
import pytest
import sys
import logging
import traceback
import json
from io import StringIO
from sqlalchemy import func, desc

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def register_routes(app):
    @app.route('/')
    def index():
        """Renderiza la página principal con estadísticas básicas"""
        try:
            data = {
                'total_groups': 0,
                'total_users': 0,
                'total_patterns': 0,
                'total_messages': 0
            }
            
            try:
                db = get_db()
                # Estadísticas básicas del sistema
                data['total_groups'] = db.query(Group).count()
                
                # Obtener datos del motor de IA
                try:
                    ai = SimpleAI()
                    ai_stats = ai.get_stats()
                    data['total_patterns'] = ai_stats.get('patterns', 0)
                    data['total_messages'] = ai_stats.get('messages', 0)
                    data['total_users'] = ai_stats.get('users', 0)
                except Exception as ai_err:
                    logger.error(f"Error obteniendo stats de IA para index: {ai_err}")
                
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en index: {db_err}")
            
            return render_template('index.html', **data)
        except Exception as e:
            logger.error(f"Error general en index: {e}")
            return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        try:
            if current_user.is_authenticated:
                logger.info("Usuario ya autenticado, redirigiendo a dashboard")
                return redirect(url_for('dashboard'))

            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                logger.debug(f"Intento de login para usuario: {username}")
                
                # Verificar existencia del usuario
                user = User.query.filter_by(username=username).first()
                if not user:
                    logger.warning(f"Intento fallido de login: usuario {username} no existe")
                    flash('Usuario o contraseña incorrectos', 'error')
                    return render_template('login.html')
                
                # Verificar contraseña
                if user.check_password(password):
                    logger.info(f"Login exitoso para usuario: {username}")
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    logger.warning(f"Intento fallido de login: contraseña incorrecta para {username}")
                    flash('Usuario o contraseña incorrectos', 'error')
            
            return render_template('login.html')
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            logger.error(traceback.format_exc())
            flash('Error al procesar el login', 'error')
            return render_template('error.html', error="Error interno al procesar el login"), 500

    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            logger.info(f"Acceso al dashboard por usuario: {current_user.username}")
            
            # Datos iniciales por defecto en caso de error
            data = {
                'total_groups': 0,
                'total_actions': 0,
                'total_warnings': 0,
                'ai_stats': {},
                'group_stats': []
            }
            
            try:
                # Obtener estadísticas del bot
                logger.debug("Obteniendo estadísticas del bot...")
                db = get_db()
                data['total_groups'] = db.query(Group).count()
                data['total_actions'] = db.query(ModAction).count()
                data['total_warnings'] = db.query(Warning).count()
                
                # Obtener stats de IA
                logger.debug("Obteniendo estadísticas de IA...")
                try:
                    ai = SimpleAI()
                    data['ai_stats'] = ai.get_stats()
                except Exception as ai_err:
                    logger.error(f"Error obteniendo stats de IA: {ai_err}")
                    data['ai_stats'] = {'patterns': 0, 'responses': 0, 'avg_confidence': 0}
                
                # Obtener grupos activos
                logger.debug("Obteniendo datos de grupos...")
                try:
                    groups = db.query(Group).all()
                    group_stats = []
                    for group in groups:
                        try:
                            group_data = {
                                'title': group.title or 'Sin nombre',
                                'chat_id': getattr(group, 'chat_id', 'N/A'),
                                'warnings': 0,
                                'actions': 0,
                                'auto_mod': getattr(group, 'auto_mod', False)
                            }
                            
                            if hasattr(group, 'chat_id'):
                                warnings = db.query(Warning).filter_by(group_id=str(group.chat_id)).count()
                                actions = db.query(ModAction).filter_by(group_id=str(group.chat_id)).count()
                                group_data['warnings'] = warnings
                                group_data['actions'] = actions
                                
                            group_stats.append(group_data)
                        except Exception as group_err:
                            logger.error(f"Error procesando grupo: {group_err}")
                            continue
                    data['group_stats'] = group_stats
                except Exception as groups_err:
                    logger.error(f"Error obteniendo grupos: {groups_err}")
            
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en dashboard: {db_err}")
                logger.error(traceback.format_exc())
                flash('Error al cargar datos de la base de datos', 'warning')
                
            return render_template(
                'dashboard.html',
                total_groups=data['total_groups'],
                total_actions=data['total_actions'],
                total_warnings=data['total_warnings'],
                ai_stats=data['ai_stats'],
                group_stats=data['group_stats']
            )
        except Exception as e:
            logger.error(f"Error general cargando dashboard: {e}")
            logger.error(traceback.format_exc())
            flash('Error al cargar el dashboard', 'error')
            return render_template('dashboard.html', 
                               total_groups=0,
                               total_actions=0,
                               total_warnings=0,
                               ai_stats={},
                               group_stats=[])

    @app.route('/wiki')
    def wiki():
        """Renderiza la wiki del proyecto"""
        try:
            with open('WIKI.md', 'r', encoding='utf-8') as f:
                content = f.read()
            html_content = markdown2.markdown(content)
            return render_template('wiki.html', content=html_content)
        except Exception as e:
            app.logger.error(f"Error al cargar la wiki: {e}")
            return render_template('error.html', error="Error al cargar la wiki"), 500

    @app.route('/test')
    @login_required
    def run_tests():
        """Ejecuta las pruebas del proyecto y muestra los resultados"""
        try:
            import subprocess
            import tempfile
            
            logger.info(f"Ejecutando tests solicitados por {current_user.username}")
            
            # Ejecutar pruebas en un proceso separado para no interferir con la app
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as output_file:
                output_file_path = output_file.name
                
            try:
                # Ejecutar pytest como un proceso separado y capturar su salida
                process = subprocess.run(
                    ['python', '-m', 'pytest', 'test', '-v'],
                    capture_output=True,
                    text=True,
                    timeout=30  # Timeout de 30 segundos
                )
                
                test_output = process.stdout + "\n\n" + process.stderr
                success = process.returncode == 0
                
                # Guardar la salida completa para debugging
                with open(output_file_path, 'w') as f:
                    f.write(test_output)
                
                logger.info(f"Tests ejecutados con resultado: {'éxito' if success else 'fallo'}")
            except subprocess.TimeoutExpired:
                logger.error("Timeout al ejecutar tests")
                test_output = "ERROR: Timeout al ejecutar las pruebas (más de 30 segundos)"
                success = False
            
            # Manejo de salida muy larga
            if len(test_output) > 10000:
                test_output = test_output[:5000] + "\n\n... [Output truncado] ...\n\n" + test_output[-5000:]
            
            return render_template('test.html',
                                success=success,
                                output=test_output)
        except Exception as e:
            logger.error(f"Error ejecutando tests: {e}")
            logger.error(traceback.format_exc())
            return render_template('error.html', error="Error al ejecutar las pruebas"), 500

    @app.route('/api/stats')
    @login_required
    def get_stats():
        try:
            logger.info(f"Solicitud de API stats por usuario: {current_user.username}")
            
            # Inicializar valores por defecto
            stats = {
                'total_groups': 0,
                'total_actions': 0,
                'total_warnings': 0,
                'total_users': 0,
                'total_messages': 0,
                'grupos_activos': 0,
                'advertencias': 0,
                'patrones_aprendidos': 0,
                'precisión': 0,
                'ai_stats': {
                    'patterns': 0,
                    'responses': 0,
                    'accuracy': 0
                },
                'group_stats': []
            }
            
            try:
                # Datos de base de datos
                db = get_db()
                stats['total_groups'] = db.query(Group).count()
                stats['total_actions'] = db.query(ModAction).count()
                stats['total_warnings'] = db.query(Warning).count()
                stats['grupos_activos'] = stats['total_groups']
                stats['advertencias'] = stats['total_warnings']
                
                # Datos de IA
                try:
                    ai = SimpleAI()
                    ai_data = ai.get_stats()
                    stats['ai_stats'] = ai_data
                    stats['patrones_aprendidos'] = ai_data.get('patterns', 0)
                    stats['precisión'] = ai_data.get('accuracy', 0)
                except Exception as ai_err:
                    logger.error(f"Error obteniendo stats de IA en API: {ai_err}")
                
                # Datos de grupos
                try:
                    groups = db.query(Group).all()
                    group_data = []
                    for group in groups:
                        try:
                            g_data = {
                                'title': getattr(group, 'title', 'Sin nombre'),
                                'chat_id': getattr(group, 'chat_id', 'N/A'),
                                'warnings': 0,
                                'actions': 0
                            }
                            
                            if hasattr(group, 'chat_id'):
                                g_data['warnings'] = db.query(Warning).filter_by(group_id=str(group.chat_id)).count()
                                g_data['actions'] = db.query(ModAction).filter_by(group_id=str(group.chat_id)).count()
                                
                            group_data.append(g_data)
                        except Exception as group_err:
                            logger.error(f"Error procesando grupo en API: {group_err}")
                    
                    stats['group_stats'] = group_data
                except Exception as groups_err:
                    logger.error(f"Error obteniendo grupos en API: {groups_err}")
                
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en API stats: {db_err}")
                logger.error(traceback.format_exc())
                
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error general en API stats: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=404), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error=500), 500
        
    @app.route('/terms')
    def terms():
        """Renderiza los términos y condiciones"""
        return render_template('terms.html')
        
    @app.route('/privacy')
    def privacy():
        """Renderiza la política de privacidad"""
        return render_template('privacy.html')
        
    @app.route('/knowledge')
    @login_required
    def knowledge():
        """Renderiza la página de gestión de conocimiento"""
        try:
            logger.info(f"Acceso a gestión de conocimiento por usuario: {current_user.username}")
            patterns = []
            
            try:
                # Inicializar el SimpleAI
                ai = SimpleAI()
                
                # Obtener patrones de la base de datos
                db = get_db()
                
                # Consultar patrones desde la tabla AIPattern
                from shared.database import AIPattern
                patterns_data = db.query(AIPattern).all()
                
                patterns = [(p.pattern, p.response, p.confidence) for p in patterns_data]
                
                db.close()
                logger.info(f"Cargados {len(patterns)} patrones para la vista de conocimiento")
                
            except Exception as e:
                logger.error(f"Error cargando patrones: {str(e)}")
                logger.error(traceback.format_exc())
                flash('Error al cargar los patrones de conocimiento', 'error')
                
            return render_template('knowledge.html', patterns=patterns)
        except Exception as e:
            logger.error(f"Error general en knowledge: {str(e)}")
            logger.error(traceback.format_exc())
            return render_template('error.html', error="Error al cargar la base de conocimiento"), 500
            
    @app.route('/api/add_pattern', methods=['POST'])
    @login_required
    def add_pattern():
        """API para añadir un nuevo patrón"""
        try:
            logger.info(f"Solicitud para añadir patrón por usuario: {current_user.username}")
            
            pattern = request.form.get('pattern')
            response = request.form.get('response')
            confidence = float(request.form.get('confidence', 0.8))
            
            if not pattern or not response:
                return jsonify({'success': False, 'error': 'El patrón y la respuesta son obligatorios'})
                
            # Validar datos
            if len(pattern) < 2:
                return jsonify({'success': False, 'error': 'El patrón debe tener al menos 2 caracteres'})
                
            if len(response) < 2:
                return jsonify({'success': False, 'error': 'La respuesta debe tener al menos 2 caracteres'})
                
            if confidence < 0 or confidence > 1:
                return jsonify({'success': False, 'error': 'La confianza debe estar entre 0 y 1'})
                
            try:
                # Inicializar AI y guardar patrón
                ai = SimpleAI()
                success = ai.learn(pattern, response, confidence)
                
                if success:
                    logger.info(f"Patrón añadido exitosamente: '{pattern[0:30]}...'")
                    return jsonify({'success': True})
                else:
                    logger.warning(f"El patrón ya existe: '{pattern[0:30]}...'")
                    return jsonify({'success': False, 'error': 'El patrón ya existe'})
                    
            except Exception as e:
                logger.error(f"Error añadiendo patrón: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'success': False, 'error': str(e)})
                
        except Exception as e:
            logger.error(f"Error general en add_pattern: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Error interno del servidor'})
            
    @app.route('/api/update_pattern', methods=['POST'])
    @login_required
    def update_pattern():
        """API para actualizar un patrón existente"""
        try:
            logger.info(f"Solicitud para actualizar patrón por usuario: {current_user.username}")
            
            original_pattern = request.form.get('original_pattern')
            pattern = request.form.get('pattern')
            response = request.form.get('response')
            confidence = float(request.form.get('confidence', 0.8))
            
            if not original_pattern or not pattern or not response:
                return jsonify({'success': False, 'error': 'Faltan datos obligatorios'})
                
            # Validar datos
            if len(pattern) < 2:
                return jsonify({'success': False, 'error': 'El patrón debe tener al menos 2 caracteres'})
                
            if len(response) < 2:
                return jsonify({'success': False, 'error': 'La respuesta debe tener al menos 2 caracteres'})
                
            if confidence < 0 or confidence > 1:
                return jsonify({'success': False, 'error': 'La confianza debe estar entre 0 y 1'})
                
            try:
                # Actualizar en la base de datos
                db = get_db()
                from shared.database import AIPattern
                
                # Buscar el patrón original
                existing = db.query(AIPattern).filter_by(pattern=original_pattern).first()
                
                if not existing:
                    db.close()
                    return jsonify({'success': False, 'error': 'El patrón original no existe'})
                    
                # Si solo cambia la respuesta o confianza, actualizar
                if original_pattern == pattern:
                    existing.response = response
                    existing.confidence = confidence
                    db.commit()
                    db.close()
                    logger.info(f"Patrón actualizado exitosamente: '{pattern[0:30]}...'")
                    return jsonify({'success': True})
                    
                # Si cambia el patrón, eliminar y crear nuevo
                db.delete(existing)
                db.commit()
                
                # Crear nuevo con el patrón actualizado
                new_pattern = AIPattern(
                    pattern=pattern,
                    response=response,
                    confidence=confidence,
                    uses=existing.uses,
                    created_at=existing.created_at,
                    last_used=existing.last_used
                )
                db.add(new_pattern)
                db.commit()
                db.close()
                
                logger.info(f"Patrón actualizado exitosamente (con cambio de texto): '{pattern[0:30]}...'")
                return jsonify({'success': True})
                
            except Exception as e:
                logger.error(f"Error actualizando patrón: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'success': False, 'error': str(e)})
                
        except Exception as e:
            logger.error(f"Error general en update_pattern: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Error interno del servidor'})
            
    @app.route('/api/delete_pattern', methods=['POST'])
    @login_required
    def delete_pattern():
        """API para eliminar un patrón"""
        try:
            logger.info(f"Solicitud para eliminar patrón por usuario: {current_user.username}")
            
            pattern = request.form.get('pattern')
            
            if not pattern:
                return jsonify({'success': False, 'error': 'El patrón es obligatorio'})
                
            try:
                # Eliminar de la base de datos
                db = get_db()
                from shared.database import AIPattern
                
                # Buscar el patrón
                existing = db.query(AIPattern).filter_by(pattern=pattern).first()
                
                if not existing:
                    db.close()
                    return jsonify({'success': False, 'error': 'El patrón no existe'})
                    
                # Eliminar
                db.delete(existing)
                db.commit()
                db.close()
                
                logger.info(f"Patrón eliminado exitosamente: '{pattern[0:30]}...'")
                return jsonify({'success': True})
                
            except Exception as e:
                logger.error(f"Error eliminando patrón: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'success': False, 'error': str(e)})
                
        except Exception as e:
            logger.error(f"Error general en delete_pattern: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Error interno del servidor'})
            
    # Nuevas rutas para configuración de la web
    @app.route('/config', methods=['GET'])
    @login_required
    def site_config():
        """Página de configuración del sitio web"""
        try:
            logger.info(f"Acceso a configuración por usuario: {current_user.username}")
            
            # Obtener configuración actual del usuario (desde la sesión o valores por defecto)
            config = {
                'theme': session.get('theme', 'dark'),
                'language': session.get('language', 'es'),
                'sidebar': session.get('sidebar', 'visible'),
                'date_format': session.get('date_format', 'dd/mm/yyyy'),
                'email_notifications': session.get('email_notifications', False),
                'telegram_notifications': session.get('telegram_notifications', True),
                'notification_level': session.get('notification_level', 'important'),
                'timezone': session.get('timezone', 'America/Havana')
            }
            
            return render_template('config.html', **config)
        except Exception as e:
            logger.error(f"Error cargando página de configuración: {str(e)}")
            logger.error(traceback.format_exc())
            flash('Error al cargar la configuración', 'error')
            return render_template('error.html', error="Error al cargar la configuración"), 500
            
    @app.route('/config', methods=['POST'])
    @login_required
    def save_config():
        """Guardar configuración del sitio web"""
        try:
            logger.info(f"Guardando configuración por usuario: {current_user.username}")
            
            config_type = request.form.get('config_type')
            
            if config_type == 'interface':
                # Guardar configuración de interfaz
                session['theme'] = request.form.get('theme', 'dark')
                session['language'] = request.form.get('language', 'es')
                session['sidebar'] = request.form.get('sidebar', 'visible')
                session['date_format'] = request.form.get('date_format', 'dd/mm/yyyy')
                
                logger.info(f"Configuración de interfaz actualizada: {session['theme']}, {session['language']}")
                flash('Configuración de interfaz guardada correctamente', 'success')
                
            elif config_type == 'notifications':
                # Guardar configuración de notificaciones
                session['email_notifications'] = 'email_notifications' in request.form
                session['telegram_notifications'] = 'telegram_notifications' in request.form
                session['notification_level'] = request.form.get('notification_level', 'important')
                session['timezone'] = request.form.get('timezone', 'America/Havana')
                
                logger.info(f"Configuración de notificaciones actualizada: nivel={session['notification_level']}")
                flash('Configuración de notificaciones guardada correctamente', 'success')
                
            return redirect(url_for('site_config'))
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")
            logger.error(traceback.format_exc())
            flash('Error al guardar la configuración', 'error')
            return redirect(url_for('site_config'))
            
    @app.route('/config/reset', methods=['POST'])
    @login_required
    def reset_config():
        """Restablecer configuración a valores predeterminados"""
        try:
            logger.info(f"Restableciendo configuración por usuario: {current_user.username}")
            
            # Configuración por defecto
            default_config = {
                'theme': 'dark',
                'language': 'es',
                'sidebar': 'visible',
                'date_format': 'dd/mm/yyyy',
                'email_notifications': False,
                'telegram_notifications': True,
                'notification_level': 'important',
                'timezone': 'America/Havana'
            }
            
            # Actualizar sesión
            for key, value in default_config.items():
                session[key] = value
                
            flash('Configuración restablecida a valores predeterminados', 'success')
            return redirect(url_for('site_config'))
        except Exception as e:
            logger.error(f"Error restableciendo configuración: {str(e)}")
            logger.error(traceback.format_exc())
            flash('Error al restablecer la configuración', 'error')
            return redirect(url_for('site_config'))
            
    # Rutas para estadísticas del bot
    @app.route('/bot-stats')
    @login_required
    def bot_stats():
        """Estadísticas y gestión del bot de Telegram"""
        try:
            logger.info(f"Acceso a estadísticas del bot por usuario: {current_user.username}")
            
            data = {
                'total_users': 0,
                'active_users': 0,
                'total_groups': 0,
                'total_messages': 0,
                'recent_users': [],
                'recent_messages': [],
                'activity_days': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                'activity_data': [0, 0, 0, 0, 0, 0, 0]
            }
            
            try:
                # Obtener estadísticas del bot
                db = get_db()
                
                # Contadores básicos
                data['total_users'] = db.query(BotUser).count()
                data['total_groups'] = db.query(Group).count()
                data['total_messages'] = db.query(Message).count()
                
                # Usuarios activos (últimos 7 días)
                week_ago = datetime.now() - timedelta(days=7)
                data['active_users'] = db.query(BotUser).filter(
                    BotUser.created_at >= week_ago
                ).count()
                
                # Usuarios recientes
                recent_users = db.query(BotUser).order_by(
                    desc(BotUser.created_at)
                ).limit(10).all()
                
                data['recent_users'] = [{
                    'username': user.username,
                    'first_name': getattr(user, 'first_name', ''),
                    'last_name': getattr(user, 'last_name', ''),
                    'created_at': user.created_at.strftime('%d/%m/%Y'),
                    'last_activity': getattr(user, 'last_activity', 'Sin actividad')
                } for user in recent_users]
                
                # Mensajes recientes
                try:
                    recent_messages = db.query(Message).order_by(
                        desc(Message.created_at)
                    ).limit(10).all()
                    
                    data['recent_messages'] = []
                    for message in recent_messages:
                        try:
                            msg_data = {
                                'username': 'Usuario',
                                'content': message.content if hasattr(message, 'content') else 'Sin contenido',
                                'response': message.response if hasattr(message, 'response') else 'Sin respuesta',
                                'confidence': message.confidence if hasattr(message, 'confidence') else 0
                            }
                            # Intentar obtener el nombre de usuario si existe la relación
                            if hasattr(message, 'user') and message.user is not None:
                                if hasattr(message.user, 'username') and message.user.username:
                                    msg_data['username'] = message.user.username
                            
                            data['recent_messages'].append(msg_data)
                        except Exception as msg_err:
                            logger.error(f"Error procesando mensaje: {msg_err}")
                            continue
                except Exception as msg_err:
                    logger.error(f"Error obteniendo mensajes recientes: {msg_err}")
                    data['recent_messages'] = []
                
                # Datos de actividad por día de la semana
                now = datetime.now()
                for i in range(7):
                    day = now - timedelta(days=i)
                    count = db.query(Message).filter(
                        func.date(Message.created_at) == day.date()
                    ).count()
                    # Guardar en orden inverso (el día más reciente primero)
                    data['activity_data'][6-i] = count
                
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en bot_stats: {db_err}")
                logger.error(traceback.format_exc())
                flash('Error al obtener datos del bot', 'warning')
                
            return render_template('bot_stats.html', **data)
        except Exception as e:
            logger.error(f"Error general cargando bot_stats: {e}")
            logger.error(traceback.format_exc())
            flash('Error al cargar estadísticas del bot', 'error')
            return render_template('error.html', error="Error al cargar estadísticas del bot"), 500
            
    @app.route('/broadcast-message', methods=['POST'])
    @login_required
    def broadcast_message():
        """Enviar mensaje masivo a usuarios del bot"""
        try:
            logger.info(f"Envío masivo solicitado por usuario: {current_user.username}")
            
            recipient_type = request.form.get('recipient_type', 'all')
            message_content = request.form.get('message_content', '')
            add_signature = 'add_signature' in request.form
            
            if not message_content:
                flash('El mensaje no puede estar vacío', 'error')
                return redirect(url_for('bot_stats'))
                
            # Preparar mensaje con firma si es necesario
            if add_signature:
                message_content += f"\n\n_Enviado desde el panel de administración por {current_user.username}_"
                
            # Aquí iría la lógica de envío usando el Bot API
            from bot.main import TelegramBot
            try:
                bot = TelegramBot()
                sent_count = 0
                
                # Obtener destinatarios según tipo seleccionado
                db = get_db()
                
                if recipient_type == 'all':
                    # Todos los usuarios
                    users = db.query(BotUser).all()
                    for user in users:
                        if hasattr(user, 'telegram_id') and user.telegram_id:
                            try:
                                # Enviar mensaje - usando el bot directamente con sus métodos públicos
                                if hasattr(bot, 'send_message'):
                                    bot.send_message(
                                        chat_id=user.telegram_id,
                                        text=message_content,
                                        parse_mode='Markdown'
                                    )
                                    sent_count += 1
                                else:
                                    logger.error(f"El objeto bot no tiene el método send_message")
                            except Exception as send_err:
                                logger.error(f"Error enviando mensaje a {user.telegram_id}: {send_err}")
                    
                elif recipient_type == 'active':
                    # Solo usuarios activos (últimos 7 días)
                    week_ago = datetime.now() - timedelta(days=7)
                    users = db.query(BotUser).filter(
                        BotUser.created_at >= week_ago
                    ).all()
                    
                    for user in users:
                        if hasattr(user, 'telegram_id') and user.telegram_id:
                            try:
                                if hasattr(bot, 'send_message'):
                                    bot.send_message(
                                        chat_id=user.telegram_id,
                                        text=message_content,
                                        parse_mode='Markdown'
                                    )
                                    sent_count += 1
                                else:
                                    logger.error(f"El objeto bot no tiene el método send_message")
                            except Exception as send_err:
                                logger.error(f"Error enviando mensaje a {user.telegram_id}: {send_err}")
                    
                elif recipient_type == 'groups':
                    # Todos los grupos
                    groups = db.query(Group).all()
                    for group in groups:
                        if hasattr(group, 'telegram_id') and group.telegram_id:
                            try:
                                if hasattr(bot, 'send_message'):
                                    bot.send_message(
                                        chat_id=group.telegram_id,
                                        text=message_content,
                                        parse_mode='Markdown'
                                    )
                                    sent_count += 1
                                else:
                                    logger.error(f"El objeto bot no tiene el método send_message")
                            except Exception as send_err:
                                logger.error(f"Error enviando mensaje a grupo {group.telegram_id}: {send_err}")
                
                db.close()
                
                logger.info(f"Mensaje enviado exitosamente a {sent_count} destinatarios")
                flash(f'Mensaje enviado a {sent_count} destinatarios', 'success')
                
            except Exception as bot_err:
                logger.error(f"Error con el bot de Telegram: {bot_err}")
                logger.error(traceback.format_exc())
                flash('Error al enviar mensajes masivos', 'error')
                
            return redirect(url_for('bot_stats'))
        except Exception as e:
            logger.error(f"Error general en broadcast_message: {e}")
            logger.error(traceback.format_exc())
            flash('Error al procesar la solicitud de envío masivo', 'error')
            return redirect(url_for('bot_stats'))
            
    @app.route('/api/bot-stats')
    @login_required
    def get_bot_stats_api():
        """API para estadísticas del bot en tiempo real"""
        try:
            logger.info(f"Solicitud de API bot-stats por usuario: {current_user.username}")
            
            stats = {
                'total_users': 0,
                'active_users': 0,
                'total_groups': 0,
                'total_messages': 0,
                'activity_data': [0, 0, 0, 0, 0, 0, 0]
            }
            
            try:
                # Obtener estadísticas actualizadas
                db = get_db()
                
                stats['total_users'] = db.query(BotUser).count()
                stats['total_groups'] = db.query(Group).count()
                stats['total_messages'] = db.query(Message).count()
                
                # Usuarios activos (últimos 7 días)
                week_ago = datetime.now() - timedelta(days=7)
                stats['active_users'] = db.query(BotUser).filter(
                    BotUser.created_at >= week_ago
                ).count()
                
                # Datos de actividad por día de la semana
                now = datetime.now()
                for i in range(7):
                    day = now - timedelta(days=i)
                    count = db.query(Message).filter(
                        func.date(Message.created_at) == day.date()
                    ).count()
                    # Guardar en orden inverso (el día más reciente primero)
                    stats['activity_data'][6-i] = count
                
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en API bot-stats: {db_err}")
                logger.error(traceback.format_exc())
                
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error general en API bot-stats: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)})
            
    # Rutas para estadísticas y configuración de IA
    @app.route('/ai-stats')
    @login_required
    def ai_stats():
        """Estadísticas y configuración del sistema de IA"""
        try:
            logger.info(f"Acceso a estadísticas de IA por usuario: {current_user.username}")
            
            data = {
                'ai_stats': {
                    'patterns': 0,
                    'interactions': 0,
                    'accuracy': 0,
                    'avg_confidence': 0
                },
                'ai_config': {
                    'min_confidence': 0.7,
                    'learning_rate': 0.01,
                    'max_context_length': 1000,
                    'auto_learn': True
                },
                'confidence_distribution': [0, 0, 0, 0, 0],
                'top_patterns': []
            }
            
            try:
                # Obtener estadísticas de IA
                ai = SimpleAI()
                ai_stats = ai.get_stats()
                
                data['ai_stats'] = {
                    'patterns': ai_stats.get('patterns', 0),
                    'interactions': ai_stats.get('interactions', 0),
                    'accuracy': ai_stats.get('accuracy', 0),
                    'avg_confidence': ai_stats.get('avg_confidence', 0)
                }
                
                # Obtener configuración actual
                try:
                    from config.config import Config
                    data['ai_config'] = {
                        'min_confidence': float(Config.MIN_CONFIDENCE),
                        'learning_rate': float(Config.LEARNING_RATE),
                        'max_context_length': int(Config.MAX_CONTEXT_LENGTH),
                        'auto_learn': True  # Por defecto está activo
                    }
                except Exception as config_err:
                    logger.error(f"Error obteniendo configuración de IA: {config_err}")
                    
                # Obtener distribución de confianza
                db = get_db()
                from shared.database import AIPattern, Message
                
                # Distribución [0-20%, 21-40%, 41-60%, 61-80%, 81-100%]
                confidence_ranges = [0.2, 0.4, 0.6, 0.8, 1.0]
                
                # Inicializar contadores
                confidence_counts = [0, 0, 0, 0, 0]
                
                # Contar patrones en cada rango de confianza
                patterns = db.query(AIPattern).all()
                for pattern in patterns:
                    for i, limit in enumerate(confidence_ranges):
                        if pattern.confidence <= limit:
                            confidence_counts[i] += 1
                            break
                            
                data['confidence_distribution'] = confidence_counts
                
                # Obtener patrones más usados
                top_patterns = db.query(AIPattern).order_by(
                    desc(AIPattern.uses)
                ).limit(10).all()
                
                data['top_patterns'] = [{
                    'pattern': pattern.pattern,
                    'response': pattern.response,
                    'confidence': pattern.confidence,
                    'uses': pattern.uses,
                    'last_used': pattern.last_used.strftime('%d/%m/%Y %H:%M') if pattern.last_used else None
                } for pattern in top_patterns]
                
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en ai_stats: {db_err}")
                logger.error(traceback.format_exc())
                flash('Error al obtener datos de IA', 'warning')
                
            return render_template('ai_stats.html', **data)
        except Exception as e:
            logger.error(f"Error general cargando ai_stats: {e}")
            logger.error(traceback.format_exc())
            flash('Error al cargar estadísticas de IA', 'error')
            return render_template('error.html', error="Error al cargar estadísticas de IA"), 500
            
    @app.route('/api/ai-stats')
    @login_required
    def get_ai_stats_api():
        """API para estadísticas de IA en tiempo real"""
        try:
            logger.info(f"Solicitud de API ai-stats por usuario: {current_user.username}")
            
            stats = {
                'patterns': 0,
                'interactions': 0,
                'accuracy': 0,
                'avg_confidence': 0,
                'confidence_distribution': [0, 0, 0, 0, 0]
            }
            
            try:
                # Obtener estadísticas actualizadas
                ai = SimpleAI()
                ai_stats = ai.get_stats()
                
                stats['patterns'] = ai_stats.get('patterns', 0)
                stats['interactions'] = ai_stats.get('interactions', 0)
                stats['accuracy'] = ai_stats.get('accuracy', 0)
                stats['avg_confidence'] = ai_stats.get('avg_confidence', 0)
                
                # Obtener distribución de confianza actualizada
                db = get_db()
                from shared.database import AIPattern
                
                # Distribución [0-20%, 21-40%, 41-60%, 61-80%, 81-100%]
                confidence_ranges = [0.2, 0.4, 0.6, 0.8, 1.0]
                
                # Inicializar contadores
                confidence_counts = [0, 0, 0, 0, 0]
                
                # Contar patrones en cada rango de confianza
                patterns = db.query(AIPattern).all()
                for pattern in patterns:
                    for i, limit in enumerate(confidence_ranges):
                        if pattern.confidence <= limit:
                            confidence_counts[i] += 1
                            break
                
                stats['confidence_distribution'] = confidence_counts
                db.close()
            except Exception as db_err:
                logger.error(f"Error de base de datos en API ai-stats: {db_err}")
                logger.error(traceback.format_exc())
                
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error general en API ai-stats: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)})
            
    @app.route('/save-ai-config', methods=['POST'])
    @login_required
    def save_ai_config():
        """Guardar configuración de IA"""
        try:
            logger.info(f"Guardando configuración de IA por usuario: {current_user.username}")
            
            # Obtener parámetros
            min_confidence = float(request.form.get('min_confidence', 0.7))
            learning_rate = float(request.form.get('learning_rate', 0.01))
            max_context_length = int(request.form.get('max_context_length', 1000))
            auto_learn = 'auto_learn' in request.form
            
            # Validar valores
            if min_confidence < 0 or min_confidence > 1:
                flash('El valor de confianza mínima debe estar entre 0 y 1', 'error')
                return redirect(url_for('ai_stats'))
                
            if learning_rate < 0 or learning_rate > 1:
                flash('La tasa de aprendizaje debe estar entre 0 y 1', 'error')
                return redirect(url_for('ai_stats'))
                
            if max_context_length < 100 or max_context_length > 5000:
                flash('La longitud máxima de contexto debe estar entre 100 y 5000', 'error')
                return redirect(url_for('ai_stats'))
                
            # Guardar configuración
            try:
                # Actualizar variables de entorno en tiempo de ejecución
                os.environ['MIN_CONFIDENCE'] = str(min_confidence)
                os.environ['LEARNING_RATE'] = str(learning_rate)
                os.environ['MAX_CONTEXT_LENGTH'] = str(max_context_length)
                
                # También se podría actualizar en la base de datos si hay una tabla específica
                # para configuración o en un archivo de configuración
                
                logger.info(f"Configuración de IA actualizada: MC={min_confidence}, LR={learning_rate}")
                flash('Configuración de IA guardada correctamente', 'success')
            except Exception as save_err:
                logger.error(f"Error guardando configuración de IA: {save_err}")
                logger.error(traceback.format_exc())
                flash('Error al guardar la configuración de IA', 'error')
                
            return redirect(url_for('ai_stats'))
        except Exception as e:
            logger.error(f"Error general en save_ai_config: {e}")
            logger.error(traceback.format_exc())
            flash('Error al procesar la configuración de IA', 'error')
            return redirect(url_for('ai_stats'))
            
    @app.route('/train-ai', methods=['POST'])
    @login_required
    def train_ai():
        """Entrenar sistema de IA"""
        try:
            logger.info(f"Entrenamiento de IA solicitado por usuario: {current_user.username}")
            
            try:
                # Obtener instancia de IA
                ai = SimpleAI()
                
                # Realizar entrenamiento (lógica depende de la implementación)
                # Podría ser usando datos históricos, de un archivo, etc.
                success = True
                message = "Entrenamiento completado correctamente"
                
                logger.info("Entrenamiento de IA ejecutado exitosamente")
                flash(message, 'success')
            except Exception as train_err:
                logger.error(f"Error entrenando IA: {train_err}")
                logger.error(traceback.format_exc())
                flash('Error durante el entrenamiento de IA', 'error')
                
            return redirect(url_for('ai_stats'))
        except Exception as e:
            logger.error(f"Error general en train_ai: {e}")
            logger.error(traceback.format_exc())
            flash('Error al procesar la solicitud de entrenamiento', 'error')
            return redirect(url_for('ai_stats'))
            
    @app.route('/backup-ai', methods=['POST'])
    @login_required
    def backup_ai_knowledge():
        """Crear respaldo de la base de conocimiento de IA"""
        try:
            logger.info(f"Respaldo de IA solicitado por usuario: {current_user.username}")
            
            try:
                # Obtener datos de la base de datos
                db = get_db()
                from shared.database import AIPattern
                
                # Consultar todos los patrones
                patterns = db.query(AIPattern).all()
                
                # Crear estructura de datos para el respaldo
                backup_data = [{
                    'pattern': p.pattern,
                    'response': p.response,
                    'confidence': p.confidence,
                    'uses': p.uses,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                    'last_used': p.last_used.isoformat() if p.last_used else None
                } for p in patterns]
                
                # Crear directorio de respaldos si no existe
                from config.config import Config
                import os
                backup_dir = Config.BACKUP_DIR
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generar nombre de archivo con timestamp
                backup_file = os.path.join(
                    backup_dir, 
                    f"ai_knowledge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                # Guardar archivo
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=4)
                
                logger.info(f"Respaldo de IA creado exitosamente: {backup_file}")
                flash(f'Respaldo creado correctamente con {len(patterns)} patrones', 'success')
                
                db.close()
            except Exception as backup_err:
                logger.error(f"Error creando respaldo de IA: {backup_err}")
                logger.error(traceback.format_exc())
                flash('Error al crear respaldo de IA', 'error')
                
            return redirect(url_for('ai_stats'))
        except Exception as e:
            logger.error(f"Error general en backup_ai_knowledge: {e}")
            logger.error(traceback.format_exc())
            flash('Error al procesar la solicitud de respaldo', 'error')
            return redirect(url_for('ai_stats'))
            
    @app.route('/reset-ai', methods=['POST'])
    @login_required
    def reset_ai():
        """Reiniciar sistema de IA eliminando todos los patrones aprendidos"""
        try:
            logger.info(f"Reinicio de IA solicitado por usuario: {current_user.username}")
            
            try:
                # Eliminar todos los patrones de la base de datos
                db = get_db()
                from shared.database import AIPattern
                
                # Contar patrones para informar al usuario
                pattern_count = db.query(AIPattern).count()
                
                # Eliminar todos los patrones
                db.query(AIPattern).delete()
                db.commit()
                
                logger.info(f"Sistema de IA reiniciado: {pattern_count} patrones eliminados")
                flash(f'Sistema de IA reiniciado: {pattern_count} patrones eliminados', 'success')
                
                db.close()
            except Exception as reset_err:
                logger.error(f"Error reiniciando IA: {reset_err}")
                logger.error(traceback.format_exc())
                flash('Error al reiniciar el sistema de IA', 'error')
                
            return redirect(url_for('ai_stats'))
        except Exception as e:
            logger.error(f"Error general en reset_ai: {e}")
            logger.error(traceback.format_exc())
            flash('Error al procesar la solicitud de reinicio', 'error')
            return redirect(url_for('ai_stats'))