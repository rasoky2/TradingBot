"""
Inicialización de la aplicación Flask
"""
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from app.config import config
from app.models import Base

# Inicialización de extensiones
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
jwt = JWTManager()


def create_app() -> Flask:
    """
    Factory para crear la aplicación Flask
    
    Returns:
        Instancia de Flask configurada
    """
    app = Flask(__name__)
    
    # Configuración de Flask
    app.config['SECRET_KEY'] = config.jwt_secret_key
    app.config['JWT_SECRET_KEY'] = config.jwt_secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    jwt.init_app(app)
    
    # Configurar CORS
    if config.cors_origins:
        CORS(app, resources={r"/api/*": {"origins": config.cors_origins}})
    else:
        CORS(app)
    
    # Configurar logging
    setup_logging()
    
    # Registrar blueprints
    from app.routes.api import api_bp
    from app.routes.web import web_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(web_bp)
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    app.logger.info(f"{config.bot_name} inicializado correctamente")
    
    return app


def setup_logging() -> None:
    """Configura el sistema de logging"""
    log_file = Path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

