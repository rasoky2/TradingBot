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
    import pandas as pd
    # Importar el Dream Team
    from app.strategies.crypto_swing_v1 import CryptoSwingV1
    from app.strategies.trend_strategy import TrendStrategy
    from app.strategies.macd_strategy import MacdStrategy
    from app.strategies.bollinger_strategy import BollingerStrategy
    
    limit = 250 
    ohlcv = exchange_service.get_ohlcv(pair, timeframe=config.timeframe, limit=limit)
    
    if not ohlcv:
        return jsonify({"error": "No hay datos suficientes", "reliability": 0}), 404
    
    df_base = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    latest_close = df_base['close'].iloc[-1]
    last_atr = 0
    
    # Lista de Estrategias a consultar
    strategy_instances = [
        {"id": "swing_v1", "name": "CryptoSwing V1 (Master)", "cls": CryptoSwingV1, "main": True},
        {"id": "trend", "name": "Classic Trend (RSI)", "cls": TrendStrategy, "main": False},
        {"id": "macd", "name": "Momentum MACD", "cls": MacdStrategy, "main": False},
        {"id": "bollinger", "name": "Volatilidad Bollinger", "cls": BollingerStrategy, "main": False}
    ]
    
    detailed_results = []
    
    # Variables globales para el resumen
    global_signal = "NEUTRAL"
    global_reliability = 50
    
    for meta in strategy_instances:
        # Copia fresca para cálculos
        df = df_base.copy()
        
        # Instanciar y Calcular
        strategy = meta["cls"](config)
        df = strategy.populate_indicators(df)
        df = strategy.populate_entry_trend(df)
        df = strategy.populate_exit_trend(df)
        
        last = df.iloc[-1]
        
        # --- Lógica de Niveles y Señales ---
        signal = "NEUTRAL"
        rec_type = "WAIT"
        
        if last.get('enter_long') == 1: 
            signal = "COMPRA"
            rec_type = "COMPRA"
        elif last.get('exit_long') == 1: 
            signal = "VENTA"
            rec_type = "VENTA"
            
        # Niveles (Estimados si no son la estrategia principal)
        # Usamos ATR si está calculado, sino aproximación 2%
        current_atr = last.get('atr_14', latest_close * 0.02)
        if meta["main"]: last_atr = current_atr # Guardar para uso global
        
        entry = latest_close
        stop = latest_close * 0.95
        target = latest_close * 1.10
        
        if meta["id"] == "swing_v1":
            # Lógica Específica ya conocida
            regime = last.get('regime', 'UNKNOWN')
            if regime == 'TREND_UP':
                entry = last.get('donchian_high_20', latest_close)
                stop = latest_close - (2.5 * current_atr)
                target = latest_close + (5.0 * current_atr) # Proyección Trend
            else:
                entry = last.get('bb_lower', latest_close)
                stop = latest_close - (2.0 * current_atr)
                target = last.get('bb_mid', latest_close)
                
        elif meta["id"] == "bollinger":
            entry = last.get('bb_lower', latest_close)
            target = last.get('bb_upper', latest_close)
            stop = entry * 0.97
            
        else:
            # Genéricos
            if signal == "COMPRA":
                stop = latest_close - (1.5 * current_atr)
                target = latest_close + (3.0 * current_atr)
            elif signal == "VENTA":
                stop = latest_close + (1.5 * current_atr)
                target = latest_close - (3.0 * current_atr)
        
        # --- Fiabilidad Dinámica (Scoring Engine) ---
        reliability = 50.0  # Base neutral
        
        # Obtenemos métricas del último DF
        curr_rsi = last.get('rsi', 50)
        curr_adx = last.get('adx', 20)
        curr_price = last['close']
        
        if meta["id"] == "swing_v1":
            # Si Trend: ADX suma puntos. Si Range: ADX bajo suma puntos.
            regime = last.get('regime', 'RANGE')
            if regime == "TREND_UP":
                reliability = 50 + (curr_adx - 25) # ADX 50 -> 75%
            else:
                # En rango, confiamos más si el RSI está en extremos
                dist_rsi = abs(curr_rsi - 50) # 0 a 50
                reliability = 40 + dist_rsi # RSI 30 -> 60%
                
        elif meta["id"] == "trend":
            # Basado puramente en RSI Strength
            # RSI 50 -> 0% fuerza. RSI 70/30 -> 100% fuerza relativa
            dist_rsi = abs(curr_rsi - 50)
            reliability = 30 + (dist_rsi * 1.5) # RSI 70 (+20) -> 60%
            
        elif meta["id"] == "bollinger":
            # Basado en proximidad a bandas (Squeeze o Touch)
            bb_upper = last.get('bb_upper', curr_price * 1.01)
            bb_lower = last.get('bb_lower', curr_price * 0.99)
            bandwidth = (bb_upper - bb_lower)
            
            # % posición en el canal (0=Low, 1=High)
            position_pct = (curr_price - bb_lower) / bandwidth if bandwidth > 0 else 0.5
            # Queremos saber cuan cerca está de los bordes
            dist_to_edge = 0.5 - abs(position_pct - 0.5) # 0 = en borde, 0.5 = centro
            
            # Si está cerca del borde (dist_to_edge -> 0), fiabilidad alta de reversión
            reliability = 85 - (dist_to_edge * 100) # Centro -> 35%, Borde -> 85%
            
        elif meta["id"] == "macd":
            # Basado en histograma
            hist = abs(last.get('macdhist', 0))
            # Normalización rápida (suponiendo precio BTC, hist ~ 10-100)
            reliability = 40 + (hist * 0.5) 

        # Ajuste final si hay señal activa (Bonus de confianza)
        if signal != "NEUTRAL":
            reliability += 15
            
        # Clipping 10-99
        reliability = max(10, min(99, int(reliability)))
        
        detailed_results.append({
            "name": meta["name"],
            "signal": signal, 
            "type": rec_type,
            "reliability": reliability,
            "levels": {
                "entry": round(entry, 2),
                "stop": round(stop, 2),
                "target": round(target, 2)
            },
            "desc": f"Señal basada en {meta['name']}",
            "is_main": meta["main"]
        })
        
        # Si es la principal, define el régimen global
        if meta["main"]:
            global_signal = signal
            # Para la global, usamos la fiabilidad del Master Strategy
            global_reliability = reliability

    # Extraer métricas resumen del Swing V1 (que siempre es el primero 0)
    swing_data = detailed_results[0]
    
    return jsonify({
        "pair": pair,
        "price": latest_close,
        "recommendation": global_signal,
        "reliability": global_reliability,
        
        # Datos Core para Header
        "regime": "MULTI-STRAT", 
        "adx": 0, # Ya está en el detalle si se quiere
        
        # LISTA COMPLETA DE ESTRATEGIAS
        "strategies": detailed_results,
        
        # Compatibilidad UI Vieja (si algo queda)
        "levels": swing_data["levels"],
        "support": swing_data["levels"]["stop"],
        "resistance": swing_data["levels"]["target"]
    })





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
