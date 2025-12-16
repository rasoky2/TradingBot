from .base_strategy import BaseStrategy

class BollingerStrategy(BaseStrategy):
    """
    Estrategia Clásica de Bandas de Bollinger (Mean Reversion)
    Compra cuando el precio está 'demasiado barato' y vende cuando está 'demasiado caro'.
    """
    
    # Swing Trading con Bollinger (Mean Reversion lento)
    minimal_roi = {
        "0": 0.08  # Objetivo: 8%
    }
    
    stoploss = -0.10
    timeframe = '1d'
    
    def populate_indicators(self, dataframe):
        closes = dataframe['close']
        
        # Bollinger Bands (Calculadas manualmente)
        sma = closes.rolling(window=20).mean()
        std = closes.rolling(window=20).std()
        
        dataframe['bb_upper'] = sma + (std * 2)
        dataframe['bb_lower'] = sma - (std * 2)
        
        return dataframe

    def populate_entry_trend(self, dataframe):
        dataframe['enter_long'] = 0
        
        # Regla MEJORADA: Reversión a la media con Confirmación
        # 1. Precio cerró por debajo de la banda inferior (Sobreventa extrema)
        # 2. La vela actual es VERDE (Intento de recuperación)
        # 3. Opcional: El cierre recuperó la banda (Cierre > Lower Band) -> Más seguro
        
        conditions = (
            (dataframe['close'].shift(1) < dataframe['bb_lower'].shift(1)) & # Ayer cayó fuerte
            (dataframe['close'] > dataframe['open']) & # Hoy es verde (freno)
            (dataframe['close'] > dataframe['bb_lower']) # Hoy recuperó el nivel
        )
        
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe):
        dataframe['exit_long'] = 0
        
        # Regla simple: Precio cruza por encima de la banda superior
        conditions = (
            (dataframe['close'] > dataframe['bb_upper'])
        )
        
        dataframe.loc[conditions, 'exit_long'] = 1
        return dataframe
