from .base_strategy import BaseStrategy
import pandas as pd
import pandas_ta as ta
import numpy as np

class RsiDivergenceStrategy(BaseStrategy):
    """
    Estrategia de Divergencia RSI (Trend Reversal)
    Detecta agotamiento de vendedores: Precio hace Lower Lows pero RSI hace Higher Lows.
    """
    
    minimal_roi = {
        "0": 0.10 # Objetivo ambicioso (reversiones suelen ser fuertes)
    }
    
    stoploss = -0.07 # 7% Stop
    timeframe = '1d'
    
    def populate_indicators(self, dataframe):
        closes = dataframe['close']
        lows = dataframe['low']
        
        # 1. RSI Clásico
        dataframe['rsi'] = ta.rsi(closes, length=14)
        
        # 2. Pivotes locales (Fractales) para detectar Mínimos
        # Un pivote Low es una vela con bajos más altos a la izquierda y derecha
        # argrelextrema es pesado, usaremos lógica vectorizada simple de pivotes de 5 velas
        
        # Mínimo de ventana de 5 
        dataframe['min_5'] = lows.rolling(window=5, center=True).min()
        
        # Es Pivot Low si el low es igual al minimo de la ventana
        dataframe['is_pivot_low'] = (lows == dataframe['min_5'])
        
        return dataframe

    def populate_entry_trend(self, dataframe):
        dataframe['enter_long'] = 0
        
        # LÓGICA DE DIVERGENCIA SIMPLIFICADA (Para estabilidad en Pandas)
        # Comparamos el RSI y Precio de HOY vs el RSI y Precio de hace 5-15 periodos
        
        # 1. Precio está cayendo (Tendencia bajista local)
        # Precio de hoy es MENOR que el precio de hace 10 velas
        price_lower = dataframe['close'] < dataframe['close'].shift(10)
        
        # 2. RSI está subiendo (Divergencia)
        # RSI de hoy es MAYOR que el RSI de hace 10 velas
        rsi_higher = dataframe['rsi'] > dataframe['rsi'].shift(10)
        
        # 3. RSI está en zona baja (sobreventa o cerca)
        rsi_oversold = dataframe['rsi'] < 40
        
        # 4. Vela de reversión (Verde)
        green_candle = dataframe['close'] > dataframe['open']
        
        conditions = (
            price_lower &
            rsi_higher &
            rsi_oversold &
            green_candle
        )
        
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe):
        dataframe['exit_long'] = 0
        
        # Salida por RSI alto (Sobrecompra)
        conditions = (
            (dataframe['rsi'] > 65)
        )
        
        dataframe.loc[conditions, 'exit_long'] = 1
        return dataframe
