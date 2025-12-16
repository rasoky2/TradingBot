"""
Configuración de la aplicación Flask Trading Bot
"""
import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Clase de configuración principal"""
    
    def __init__(self, config_file: str = "config.json"):
        # Determinar la ruta base (directorio flask-trading-bot)
        base_dir = Path(__file__).resolve().parent.parent
        self.config_file = str(base_dir / config_file)
        self._config: dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Carga la configuración desde el archivo JSON"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value
    
    @property
    def bot_name(self) -> str:
        return self.get('bot_name', 'FlaskTradingBot')
    
    @property
    def dry_run(self) -> bool:
        """
        Modo Recomendación (Advisor).
        Siempre True para asegurar que NUNCA ejecute órdenes reales.
        """
        return True
    
    @property
    def stake_currency(self) -> str:
        return self.get('stake_currency', 'USDT')
    
    @property
    def stake_amount(self) -> float:
        return self.get('stake_amount', 100.0)
    
    @property
    def max_open_trades(self) -> int:
        return self.get('max_open_trades', 3)
    
    @property
    def exchange_name(self) -> str:
        return self.get('exchange.name', 'binance')
    
    @property
    def exchange_key(self) -> str:
        return self.get('exchange.key', '')
    
    @property
    def exchange_secret(self) -> str:
        return self.get('exchange.secret', '')
    
    @property
    def timeframe(self) -> str:
        return self.get('timeframe', '5m')
    
    @property
    def pairlist(self) -> list[str]:
        return self.get('pairlist', [])
    
    @property
    def stoploss(self) -> float:
        return self.get('stoploss', -0.10)
    
    @property
    def minimal_roi(self) -> dict[str, float]:
        return self.get('minimal_roi', {})
    
    @property
    def strategy_name(self) -> str:
        return self.get('strategy', 'SampleStrategy')
    
    @property
    def api_enabled(self) -> bool:
        return self.get('api.enabled', True)
    
    @property
    def api_host(self) -> str:
        return self.get('api.host', '127.0.0.1')
    
    @property
    def api_port(self) -> int:
        return self.get('api.port', 5000)
    
    @property
    def jwt_secret_key(self) -> str:
        return self.get('api.jwt_secret_key', 'change-this-secret-key')
    
    @property
    def cors_origins(self) -> list[str]:
        return self.get('api.cors_origins', [])
    
    @property
    def database_url(self) -> str:
        # Prioridad: 1. db_url en json, 2. database.url en json, 3. Defecto absoluto
        val = self.get('db_url') or self.get('database.url')
        if val:
            return val
            
        # Construir ruta absoluta por defecto: flask-trading-bot/user_data/tradesv3.sqlite
        base_dir = Path(__file__).resolve().parent.parent
        db_path = base_dir / 'user_data' / 'tradesv3.sqlite'
        return f"sqlite:///{db_path.as_posix()}"
    
    @property
    def log_level(self) -> str:
        return self.get('logging.level', 'INFO')
    
    @property
    def log_file(self) -> str:
        val = self.get('logging.file')
        if val:
            return val
            
        # Construir ruta absoluta por defecto para logs
        base_dir = Path(__file__).resolve().parent.parent
        return str(base_dir / 'user_data' / 'logs' / 'bot.log')
    
    def to_dict(self) -> dict[str, Any]:
        """Retorna la configuración completa como diccionario"""
        return self._config.copy()


# Instancia global de configuración
config = Config()
