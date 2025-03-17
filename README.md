# LBA IA Bot - Documentación Completa 📚

## 📋 Tabla de Contenidos
- [Introducción](#introducción)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Características](#características)
- [Panel de Administración](#panel-de-administración)
- [Sistema de IA](#sistema-de-ia)
- [Moderación](#moderación)
- [Desarrollo](#desarrollo)
- [API y Endpoints](#api-y-endpoints)
- [Contribución](#contribución)

## 🎯 Introducción
LBA IA Bot es un bot de Telegram avanzado que combina inteligencia artificial con capacidades de moderación y gestión de grupos. El bot incluye un panel de administración web para monitoreo y configuración en tiempo real.

### Características Principales
- 🤖 IA adaptativa para respuestas automáticas
- 🔍 Búsqueda web y Wikipedia integrada
- 👥 Moderación automática de grupos
- 📊 Panel de estadísticas en tiempo real
- 💾 Sistema de respaldo automático
- 🔄 Aprendizaje continuo

## 🚀 Instalación

### Requisitos Previos
- Python 3.8+
- PostgreSQL
- Token de Bot de Telegram
- Conexión a Internet

### Pasos de Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Lean031110/lba_ia_bot.git
   cd lba_ia_bot
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   Crear archivo `.env` con:
   ```env
   BOT_TOKEN=tu_token_aqui
   CREATOR_ID=tu_id_aqui
   BOT_USERNAME=nombre_del_bot
   LEARNING_RATE=0.01
   MIN_CONFIDENCE=0.7
   MAX_CONTEXT_LENGTH=1000
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_db
   SESSION_SECRET=tu_clave_secreta
   ```

## ⚙️ Configuración

### Base de Datos
El bot utiliza PostgreSQL. La estructura se crea automáticamente al iniciar, incluyendo:
- Tabla `users`: Información de usuarios
- Tabla `knowledge`: Base de conocimiento de IA
- Tabla `chat_history`: Historial de interacciones
- Tabla `groups`: Configuración de grupos

### Entrenamiento de IA
Para entrenar al bot con datos personalizados:
1. Modificar `data/training_data.json` con nuevos patrones
2. Ejecutar el entrenamiento:
   ```bash
   python tools/train_bot.py data/training_data.json
   ```

## 🎮 Uso

### Iniciar el Bot
```bash
python main.py
```

### Iniciar Panel Web
```bash
gunicorn --bind 0.0.0.0:5000 web.app:app
```

### Comandos del Bot

#### Comandos Básicos
- `/start` - Inicia el bot
- `/help` - Muestra ayuda
- `/info` - Información del bot
- `/search` - Realiza búsquedas
- `/wiki` - Busca en Wikipedia

#### Comandos de Administración
- `/config` - Configura el bot
- `/stats` - Muestra estadísticas
- `/train` - Entrena la IA
- `/backup` - Crea respaldo
- `/broadcast` - Envía mensaje masivo

#### Comandos de Grupo
- `/welcome` - Configura mensaje de bienvenida
- `/rules` - Establece reglas
- `/warn` - Advierte a un usuario
- `/unwarn` - Quita advertencia
- `/ban` - Banea usuario
- `/unban` - Desbanea usuario

## 🖥️ Panel de Administración

### Funcionalidades
- Dashboard con estadísticas en tiempo real
- Gráficos interactivos de actividad
- Gestión de usuarios y grupos
- Configuración de IA
- Sistema de respaldos
- Logs en tiempo real

### Secciones
1. **Dashboard**
   - Contadores en tiempo real
   - Gráficos de actividad
   - Métricas de rendimiento

2. **Usuarios**
   - Lista de usuarios
   - Estadísticas individuales
   - Acciones de moderación

3. **Grupos**
   - Configuración por grupo
   - Estadísticas
   - Reglas y mensajes

4. **IA**
   - Entrenamiento manual
   - Visualización de patrones
   - Ajuste de parámetros

5. **Configuración**
   - Ajustes generales
   - Backup y restauración
   - Logs del sistema

## 🧠 Sistema de IA

### Funcionamiento
El bot utiliza procesamiento de lenguaje natural con las siguientes características:
- Vectorización de texto (TF-IDF)
- Similitud coseno para matching
- Sistema de confianza adaptativo
- Aprendizaje continuo

### Parámetros Configurables
- `LEARNING_RATE`: Velocidad de aprendizaje
- `MIN_CONFIDENCE`: Confianza mínima para respuestas
- `MAX_CONTEXT_LENGTH`: Longitud máxima de contexto

## 👮‍♂️ Moderación

### Características
- Detección automática de spam
- Sistema de advertencias
- Gestión de reglas por grupo
- Filtros de contenido personalizables
- Registro de acciones

### Configuración
Cada grupo puede tener su propia configuración de:
- Reglas
- Mensajes de bienvenida
- Niveles de advertencia
- Filtros de contenido

## 💻 Desarrollo

### Estructura del Proyecto
```
lba_ia_bot/
├── core/           # Núcleo del bot
├── handlers/       # Manejadores de comandos
├── web/           # Panel de administración
├── utils/         # Utilidades
├── config/        # Configuración
├── data/          # Datos y respaldos
└── tools/         # Herramientas
```

### Flujo de Trabajo
1. Instalar dependencias
2. Configurar variables de entorno
3. Inicializar base de datos
4. Ejecutar scripts de entrenamiento
5. Iniciar bot y panel web

### Tests
```bash
pytest
```

## 🔌 API y Endpoints

### Endpoints Web
- `/` - Página principal
- `/login` - Inicio de sesión
- `/dashboard` - Panel principal
- `/stats` - Estadísticas
- `/wiki` - Documentación
- `/api/stats` - API de estadísticas

### API del Bot
- Endpoints para webhooks
- Callbacks de Telegram
- Manejo de eventos

## 🤝 Contribución

### Pasos para Contribuir
1. Fork del repositorio
2. Crear rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Añadir característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

### Guías de Contribución
- Seguir PEP 8
- Documentar código nuevo
- Añadir tests
- Mantener compatibilidad

## 📄 Licencia
Este proyecto está bajo la Licencia MIT.

