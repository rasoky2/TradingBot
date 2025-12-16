"""
Servicio de integración con Exchanges vía CCXT
Migrado y simplificado desde Freqtrade
"""
import logging
from typing import Any

import ccxt

from app.config import config

logger = logging.getLogger(__name__)


class ExchangeService:
    """
    Servicio para interactuar con exchanges de criptomonedas
    Usa CCXT para comunicación unificada
    """
    
    def __init__(self):
        self._exchange: ccxt.Exchange | None = None
        self._exchange_name = config.exchange_name
        self._api_key = config.exchange_key
        self._api_secret = config.exchange_secret
        self._init_exchange()
    
    def _init_exchange(self) -> None:
        """Inicializa la conexión con el exchange"""
        try:
            exchange_class = getattr(ccxt, self._exchange_name)
            
            # Configuración básica sin keys por defecto
            exchange_config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            }
            
            # Solo agregar keys si existen
            if self._api_key and self._api_secret:
                exchange_config['apiKey'] = self._api_key
                exchange_config['secret'] = self._api_secret
            else:
                logger.info(f"Iniciando {self._exchange_name} en modo PÚBLICO (Sin API Keys)")
            
            
            self._exchange = exchange_class(exchange_config)
            
            # Cargar mercados (datos públicos)
            try:
                self._exchange.load_markets()
                logger.info(f"Exchange {self._exchange_name} inicializado correctamente")
            except Exception as e:
                logger.warning(f"Advertencia cargando mercados: {e}")
            
        except Exception as e:
            logger.error(f"Error al inicializar exchange: {e}")
            # No lanzar error, permitir intentar de nuevo o funcionar parcialmente

    
    @property
    def exchange(self) -> ccxt.Exchange:
        """Retorna la instancia del exchange"""
        if not self._exchange:
            self._init_exchange()
        return self._exchange
    
    def _ensure_markets_loaded(self) -> None:
        """Asegura que los mercados estén cargados"""
        if not hasattr(self.exchange, 'markets') or not self.exchange.markets:
            try:
                self.exchange.load_markets()
                logger.info(f"Mercados cargados para {self._exchange_name}")
            except Exception as e:
                logger.warning(f"No se pudieron cargar mercados: {e}")
    
    def get_balance(self, currency: str | None = None) -> dict[str, Any]:
        """
        Obtiene el balance de la cuenta
        
        Args:
            currency: Moneda específica (opcional)
            
        Returns:
            Diccionario con balances
        """
        try:
            balance = self.exchange.fetch_balance()
            
            if currency:
                return {
                    'currency': currency,
                    'free': balance.get(currency, {}).get('free', 0),
                    'used': balance.get(currency, {}).get('used', 0),
                    'total': balance.get(currency, {}).get('total', 0),
                }
            
            # Filtrar solo monedas con balance > 0
            filtered_balance = {}
            for curr, data in balance.items():
                if curr not in ['free', 'used', 'total', 'info'] and data.get('total', 0) > 0:
                    filtered_balance[curr] = {
                        'free': data.get('free', 0),
                        'used': data.get('used', 0),
                        'total': data.get('total', 0),
                    }
            
            return filtered_balance
            
        except Exception as e:
            logger.error(f"Error al obtener balance: {e}")
            return {}
    
    def get_ticker(self, pair: str) -> dict[str, Any]:
        """
        Obtiene el ticker de un par
        
        Args:
            pair: Par de trading (ej: BTC/USDT)
            
        Returns:
            Datos del ticker
        """
        try:
            ticker = self.exchange.fetch_ticker(pair)
            return {
                'symbol': ticker['symbol'],
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'volume': ticker.get('baseVolume'),
                'timestamp': ticker.get('timestamp'),
            }
        except Exception as e:
            logger.error(f"Error al obtener ticker de {pair}: {e}")
            return {}
    
    def get_ohlcv(
        self,
        pair: str,
        timeframe: str = '5m',
        limit: int = 100
    ) -> list[list]:
        """
        Obtiene datos OHLCV (velas) de un par
        
        Args:
            pair: Par de trading
            timeframe: Timeframe (1m, 5m, 15m, 1h, etc.)
            limit: Cantidad de velas
            
        Returns:
            Lista de velas [timestamp, open, high, low, close, volume]
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logger.error(f"Error al obtener OHLCV de {pair}: {e}")
            return []
    
    def create_order(
        self,
        pair: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None
    ) -> dict[str, Any]:
        """
        Crea una orden en el exchange
        
        Args:
            pair: Par de trading
            order_type: Tipo de orden (market, limit)
            side: Lado (buy, sell)
            amount: Cantidad
            price: Precio (solo para limit orders)
            
        Returns:
            Datos de la orden creada
        """
        try:

            # ADVISOR MODE: Siempre simular órdenes
            # Ya no existen órdenes reales en esta versión
            logger.info(
                f"[ADVISOR] Simulación de orden {side} {order_type}: "
                f"{amount} {pair} @ {price if price else 'market'}"
            )
            return {
                'id': f'sim_{pair}_{side}_{amount}',
                'symbol': pair,
                'type': order_type,
                'side': side,
                'amount': amount,
                'price': price,
                'status': 'closed',
                'filled': amount,
            }

            
        except Exception as e:
            logger.error(f"Error al crear orden: {e}")
            raise
    
    def cancel_order(self, order_id: str, pair: str) -> dict[str, Any]:
        """
        Cancela una orden
        
        Args:
            order_id: ID de la orden
            pair: Par de trading
            
        Returns:
            Datos de la orden cancelada
        """
        try:
            # ADVISOR MODE
            logger.info(f"[ADVISOR] Cancelando orden {order_id}")
            return {'id': order_id, 'status': 'canceled'}
            
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {e}")
            raise
    
    def fetch_order(self, order_id: str, pair: str) -> dict[str, Any]:
        """
        Obtiene información de una orden
        
        Args:
            order_id: ID de la orden
            pair: Par de trading
            
        Returns:
            Datos de la orden
        """
        try:
            order = self.exchange.fetch_order(order_id, pair)
            return order
        except Exception as e:
            logger.error(f"Error al obtener orden {order_id}: {e}")
            return {}
    
    def get_fee(self, pair: str, order_type: str = 'limit', side: str = 'buy') -> float:
        """
        Obtiene la comisión del exchange para un par
        
        Args:
            pair: Par de trading
            order_type: Tipo de orden
            side: Lado
            
        Returns:
            Comisión como decimal (ej: 0.001 = 0.1%)
        """
        try:
            market = self.exchange.market(pair)
            if order_type == 'market':
                return market.get('taker', 0.001)
            else:
                return market.get('maker', 0.001)
        except Exception as e:
            logger.error(f"Error al obtener fee: {e}")
            return 0.001  # Default 0.1%
    
    def get_markets(self) -> list[str]:
        """Retorna lista de mercados disponibles"""
        try:
            return list(self.exchange.markets.keys())
        except Exception as e:
            logger.error(f"Error al obtener mercados: {e}")
            return []
    
    def validate_pair(self, pair: str) -> bool:
        """Valida si un par existe en el exchange"""
        return pair in self.exchange.markets


# Instancia global del servicio (lazy loading)
_exchange_service_instance = None

def get_exchange_service() -> ExchangeService:
    """Obtiene la instancia global del servicio de exchange"""
    global _exchange_service_instance
    if _exchange_service_instance is None:
        _exchange_service_instance = ExchangeService()
    return _exchange_service_instance

# Para compatibilidad con código existente
exchange_service = get_exchange_service()
