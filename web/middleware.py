"""
Middleware para la aplicación web
Proporciona funcionalidad para logging, monitoreo y seguridad
"""
import time
import logging
from functools import wraps
from flask import request, g, session
from datetime import datetime

# Configurar logger para API
logger = logging.getLogger('web')

def api_logger_middleware(app):
    """Middleware para registrar todas las solicitudes a la API"""
    @app.before_request
    def before_request():
        # Guardar tiempo de inicio para calcular duración
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}-{id(request)}"
        
        logger.info(f"Inicio de solicitud: {request.method} {request.path}")
        
    @app.after_request
    def after_request(response):
        if not hasattr(g, 'start_time'):
            return response
            
        # Calcular tiempo de respuesta
        duration = time.time() - g.start_time
        status_code = response.status_code
        
        # Obtener ID del usuario si está autenticado
        user_id = session.get('user_id', None) if session else None
        
        # Registrar detalles de la solicitud
        if hasattr(logger, 'log_api'):
            logger.log_api(
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                response_time=duration,
                user_id=user_id,
                ip=request.remote_addr,
                user_agent=request.user_agent.string if request.user_agent else None,
                request_id=g.request_id if hasattr(g, 'request_id') else None
            )
        else:
            # Registrar utilizando el logger normal si no está disponible log_api
            logger.info(
                f"API: {request.method} {request.path} {status_code} en {duration:.4f}s",
                extra={
                    'api_call': True,
                    'endpoint': request.path,
                    'method': request.method,
                    'status_code': status_code,
                    'response_time': duration,
                    'user_id': user_id,
                    'ip': request.remote_addr
                }
            )
        
        return response

def performance_logger(endpoint_name=None):
    """Decorador para medir y registrar el rendimiento de funciones específicas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            function_name = endpoint_name or f.__name__
            
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Registrar tiempo de ejecución
            perf_logger = logging.getLogger('performance')
            
            if hasattr(perf_logger, 'info'):
                perf_logger.info(
                    f"Performance: {function_name} tomó {duration:.4f}s",
                    extra={
                        'performance': True,
                        'function': function_name,
                        'execution_time': duration,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            
            return result
        return decorated_function
    return decorator

def db_logger(operation=None, table=None):
    """Decorador para registrar operaciones de base de datos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            op = operation or f.__name__
            db_table = table
            
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Intentar obtener nombre de tabla si no se proporcionó
            if not db_table and hasattr(args[0], '__tablename__'):
                db_table = args[0].__tablename__
            elif not db_table and len(args) > 0 and hasattr(args[0], '__class__') and hasattr(args[0].__class__, '__tablename__'):
                db_table = args[0].__class__.__tablename__
            else:
                db_table = "unknown_table"
            
            # Registrar operación
            db_logger = logging.getLogger('database')
            
            if hasattr(logger, 'log_db'):
                logger.log_db(
                    operation=op,
                    table=db_table,
                    execution_time=duration,
                    result_type=type(result).__name__
                )
            else:
                # Usar logger normal si no está disponible log_db
                db_logger.info(
                    f"DB: {op} en {db_table} completado en {duration:.4f}s",
                    extra={
                        'database': True,
                        'operation': op,
                        'table': db_table,
                        'execution_time': duration
                    }
                )
            
            return result
        return decorated_function
    return decorator

def setup_middleware(app):
    """Configura todos los middleware necesarios para la aplicación"""
    # Registrar middleware de logging
    api_logger_middleware(app)
    
    # Configurar otras métricas y middleware si es necesario
    logger.info("Middleware configurado exitosamente")