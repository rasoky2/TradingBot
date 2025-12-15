"""
API REST del Trading Bot
Migrado desde Freqtrade FastAPI a Flask
"""
import logging
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from app import db
from app.config import config
from app.models import Order, Trade
from app.services import exchange_service
from app.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


def handle_errors(f):
    """Decorator para manejo de errores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {f.__name__}: {e}")
            return jsonify({"error": str(e)}), 500
    return decorated_function


# ============================================================================
# ENDPOINTS PÚBLICOS (sin autenticación)
# ============================================================================

@api_bp.route('/ping', methods=['GET'])
def ping():
    """Health check"""
    return jsonify({"status": "pong"})


@api_bp.route('/version', methods=['GET'])
def version():
    """Información de versión"""
    return jsonify({
        "bot_name": config.bot_name,
        "version": "1.0.0",
        "api_version": "1.0"
    })


@api_bp.route('/login', methods=['POST'])
@handle_errors
def login():
    """
    Login para obtener JWT token
    Body: {"username": "admin", "password": "password"}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # TODO: Implementar autenticación real
    if username == 'admin' and password == 'admin':
        access_token = create_access_token(identity=username)
        return jsonify({"access_token": access_token})
    
    return jsonify({"error": "Credenciales inválidas"}), 401


# ============================================================================
# ENDPOINTS PROTEGIDOS (requieren JWT)
# ============================================================================

@api_bp.route('/balance', methods=['GET'])
@jwt_required()
@handle_errors
def balance():
    """
    Obtiene el balance de la cuenta
    """
    currency = request.args.get('currency')
    balance_data = exchange_service.get_balance(currency)
    
    return jsonify({
        "currencies": balance_data,
        "total": len(balance_data),
        "stake_currency": config.stake_currency
    })



@api_bp.route('/status', methods=['GET'])
@handle_errors
def status():
    """
    Estado del bot y trades abiertos
    """
    open_trades = Trade.get_open_trades()
    
    return jsonify({
        "status": "running" if open_trades else "idle",
        "dry_run": config.dry_run,
        "max_open_trades": config.max_open_trades,
        "open_trades": len(open_trades),
        "trades": [trade.to_dict(include_orders=False) for trade in open_trades]
    })





@api_bp.route('/analysis/<path:pair>', methods=['GET'])
@handle_errors
def analyze_pair(pair: str):
    """
    Analiza un par usando TODAS las estrategias disponibles
    Devuelve una "Matriz de Decisiones" para el Dashboard
    """
    result = analysis_service.analyze_pair(pair)
    
    if not result:
         return jsonify({"error": "No hay datos suficientes", "reliability": 0}), 404
         
    return jsonify(result)





@api_bp.route('/ticker/<path:pair>', methods=['GET'])
@handle_errors
def ticker(pair: str):
    """
    Obtiene el ticker de un par
    """
    ticker_data = exchange_service.get_ticker(pair)
    
    if not ticker_data:
        return jsonify({"error": f"No se pudo obtener ticker de {pair}"}), 404
    
    return jsonify(ticker_data)


@api_bp.route('/ohlcv/<path:pair>', methods=['GET'])
@handle_errors
def ohlcv(pair: str):
    """
    Obtiene datos OHLCV de un par
    Query params: timeframe, limit
    """
    timeframe = request.args.get('timeframe', config.timeframe)
    limit = request.args.get('limit', 200, type=int) # Aumentado default a 200 para gráficos
    
    ohlcv_data = exchange_service.get_ohlcv(pair, timeframe, limit)
    
    return jsonify({
        "pair": pair,
        "timeframe": timeframe,
        "data": ohlcv_data
    })



@api_bp.route('/markets', methods=['GET'])
@jwt_required()
@handle_errors
def markets():
    """
    Lista de mercados disponibles
    """
    markets_list = exchange_service.get_markets()
    
    # Filtrar por stake currency si se especifica
    stake_currency = request.args.get('stake_currency', config.stake_currency)
    if stake_currency:
        markets_list = [m for m in markets_list if m.endswith(f'/{stake_currency}')]
    
    return jsonify({
        "markets": markets_list,
        "total": len(markets_list)
    })


@api_bp.route('/config', methods=['GET'])
@jwt_required()
@handle_errors
def get_config():
    """
    Configuración del bot (sin datos sensibles)
    """
    safe_config = {
        "bot_name": config.bot_name,
        "dry_run": config.dry_run,
        "stake_currency": config.stake_currency,
        "stake_amount": config.stake_amount,
        "max_open_trades": config.max_open_trades,
        "exchange": config.exchange_name,
        "timeframe": config.timeframe,
        "pairlist": config.pairlist,
        "stoploss": config.stoploss,
        "strategy": config.strategy_name,
    }
    
    return jsonify(safe_config)


# ============================================================================
# ENDPOINTS DE CONTROL (START/STOP/FORCEBUY/FORCESELL)
# ============================================================================

@api_bp.route('/start', methods=['POST'])
@jwt_required()
@handle_errors
def start_bot():
    """
    Inicia el bot de trading
    TODO: Implementar lógica de inicio
    """
    return jsonify({"message": "Bot iniciado", "status": "running"})


@api_bp.route('/stop', methods=['POST'])
@jwt_required()
@handle_errors
def stop_bot():
    """
    Detiene el bot de trading
    TODO: Implementar lógica de parada
    """
    return jsonify({"message": "Bot detenido", "status": "stopped"})


@api_bp.route('/forcebuy', methods=['POST'])
@jwt_required()
@handle_errors
def forcebuy():
    """
    Fuerza una compra
    Body: {"pair": "BTC/USDT", "price": 50000 (opcional)}
    TODO: Implementar lógica de compra forzada
    """
    data = request.get_json()
    pair = data.get('pair')
    price = data.get('price')
    
    if not pair:
        return jsonify({"error": "Par requerido"}), 400
    
    return jsonify({
        "message": f"Compra forzada de {pair}",
        "pair": pair,
        "price": price
    })


@api_bp.route('/forcesell', methods=['POST'])
@jwt_required()
@handle_errors
def forcesell():
    """
    Fuerza una venta
    Body: {"trade_id": 1}
    TODO: Implementar lógica de venta forzada
    """
    data = request.get_json()
    trade_id = data.get('trade_id')
    
    if not trade_id:
        return jsonify({"error": "trade_id requerido"}), 400
    
    trade = Trade.get_trade_by_id(trade_id)
    
    if not trade:
        return jsonify({"error": "Trade no encontrado"}), 404
    
    if not trade.is_open:
        return jsonify({"error": "Trade ya está cerrado"}), 400
    
    return jsonify({
        "message": f"Venta forzada del trade {trade_id}",
        "trade_id": trade_id
    })
