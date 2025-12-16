"""
Rutas web para el dashboard
"""
from flask import Blueprint, render_template

from app.config import config
from app.models import Trade

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('dashboard.html', config=config)





@web_bp.route('/config')
def config_page():
    """Página de configuración"""
    return render_template('config.html', config=config)
