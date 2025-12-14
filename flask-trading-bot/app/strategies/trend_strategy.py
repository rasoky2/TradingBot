from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class TrendStrategy(BaseStrategy):
    """
    Estrategia de Tendencia + Momentum (Versión Pandas Puro)
    Combina RSI y Bollinger Bands sin dependencias externas pesadas.
    """
    # Configuración SWING TRADING (4H)
    # Buscamos movimientos del 3% al 10% en días
    minimal_roi = {
        "2880": 0.01, # Dsp de 2 dias (48h*60), aceptar 1%
        "1440": 0.03, # Dsp de 1 dia, aceptar 3%
        "720": 0.05,  # Dsp de 12h, aceptar 5%
        "0": 0.10     # Aceptar 10% inmediato
    }
    
    stoploss = -0.10  # 10% Stoploss (Swing da espacio)
    timeframe = '1d'  # Gráfico de 1 Día (24h)
    
    def populate_indicators(self, dataframe):
        closes = dataframe['close']
        
        # 1. RSI (Manual calculation)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        dataframe['rsi'] = 100 - (100 / (1 + rs))
        
        # 2. Bollinger Bands (Manual calculation)
        sma = closes.rolling(window=20).mean()
        std = closes.rolling(window=20).std()
        dataframe['bb_upper'] = sma + (std * 2)
        dataframe['bb_lower'] = sma - (std * 2)
        dataframe['bb_middle'] = sma
        
        # 3. SMA Shorts & Longs
        dataframe['sma_50'] = closes.rolling(window=50).mean()
        
        return dataframe

    def populate_entry_trend(self, dataframe):
        dataframe['enter_long'] = 0
        
        # Regla: RSI bajo (<35) Y Precio tocando banda inferior
        conditions = (
            (dataframe['rsi'] < 35) &
            (dataframe['close'] <= dataframe['bb_lower'])
        )
        
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe):
        dataframe['exit_long'] = 0
        
        # Regla: RSI alto (>70) O Precio tocando banda superior
        conditions = (
            (dataframe['rsi'] > 70) |
            (dataframe['close'] >= dataframe['bb_upper'])
        )
        
        dataframe.loc[conditions, 'exit_long'] = 1
        return dataframe
