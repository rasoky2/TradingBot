from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class TurtleSoupStrategy(BaseStrategy):
    """
    Estrategia Turtle Soup (Liquidity Sweep Reversal)
    Concepto: Cazar la liquidez debajo de mínimos recientes (Fake Breakouts).
    Ideal para comprar fondos locales cuando el mercado saca a los "manos débiles".
    """
    
    # Esta estrategia busca puntos de giro precisos, stoploss ajustado
    minimal_roi = {
        "2880": 0.05, # +5% en 2 dias
        "1440": 0.03, 
        "0": 0.06     # objetivo rápido 6%
    }
    
    stoploss = -0.05  # Stop muy corto (5%). Si falla el rebote, salimos rápido.
    timeframe = '1d'
    
    def populate_indicators(self, dataframe):
        mins = dataframe['low']
        
        # Canal de Donchian de 20 periodos (Mínimos de 20 días)
        # Shift(1) porque queremos el mínimo de los 20 dias ANTERIORES a hoy
        dataframe['donchian_low_20'] = mins.rolling(window=20).min().shift(1)
        
        return dataframe

    def populate_entry_trend(self, dataframe):
        dataframe['enter_long'] = 0
        
        # CONDICIONES TURTLE SOUP BUY:
        # 1. El precio actual bajó MÁS que el mínimo de 20 días (sweep)
        # 2. PERO... logró cerrar POR ENCIMA de ese mínimo antiguo (reclaim)
        # Esto indica rechazo de precios bajos y captura de liquidez.
        
        conditions = (
            (dataframe['low'] < dataframe['donchian_low_20']) & # Violación del mínimo (Sweep)
            (dataframe['close'] > dataframe['donchian_low_20']) & # Cierre arriba (Reclaim)
            (dataframe['close'] > dataframe['open']) # Vela verde para confirmar fuerza
        )
        
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe):
        dataframe['exit_long'] = 0
        
        # Salida simple: 
        # Si cerramos por debajo del mínimo de ayer (falla el momentum)
        # O dejamos que actúe el ROI/Stoploss
        
        conditions = (
            (dataframe['close'] < dataframe['low'].shift(1))
        )
        
        dataframe.loc[conditions, 'exit_long'] = 1
        return dataframe
