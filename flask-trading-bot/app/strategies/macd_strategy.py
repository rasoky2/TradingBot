from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class MacdStrategy(BaseStrategy):
    """
    Estrategia MACD (Trend Following)
    Ideal para capturar movimientos largos de precio, no solo rebotes.
    """
    
    # Configuración SWING - MACD busca catch tendencias largas
    minimal_roi = {
        "2880": 0.05, # Despues de 48h, asegurar 5%
        "1440": 0.10, # Despues de 24h, asegurar 10%
        "0": 0.15     # Objetivo: 15%
    }
    
    stoploss = -0.15 # 15% Stoploss (Damos mucho margen)
    timeframe = '1d'
    
    def populate_indicators(self, dataframe):
        closes = dataframe['close']
        
        # 1. MACD Manual (12, 26, 9)
        # EMA 12
        ema12 = closes.ewm(span=12, adjust=False).mean()
        # EMA 26
        ema26 = closes.ewm(span=26, adjust=False).mean()
        
        # MACD Line = EMA12 - EMA26
        dataframe['macd'] = ema12 - ema26
        
        # Signal Line = EMA9 del MACD
        dataframe['macdsignal'] = dataframe['macd'].ewm(span=9, adjust=False).mean()
        
        # Histograma (Para ver fuerza)
        dataframe['macdhist'] = dataframe['macd'] - dataframe['macdsignal']
        
        return dataframe

    def populate_entry_trend(self, dataframe):
        dataframe['enter_long'] = 0
        
        # CRUCE DE ORO (Golden Cross)
        # MACD cruza por encima de la Señal
        # Y el MACD es negativo (estamos "baratos" pero subiendo)
        
        conditions = (
            (dataframe['macd'] > dataframe['macdsignal']) & # Cruce alcista
            (dataframe['macd'].shift(1) <= dataframe['macdsignal'].shift(1)) & # Confirmación de cruce
            (dataframe['macd'] < 0) # Entrar al inicio de la recuperación
        )
        
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe):
        dataframe['exit_long'] = 0
        
        # CRUCE DE LA MUERTE (Death Cross)
        # MACD cruza por debajo de la señal
        
        conditions = (
            (dataframe['macd'] < dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) >= dataframe['macdsignal'].shift(1))
        )
        
        dataframe.loc[conditions, 'exit_long'] = 1
        return dataframe
