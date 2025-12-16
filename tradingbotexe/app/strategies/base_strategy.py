"""
Base Strategy Class
Sigue la estructura estándar de Freqtrade para facilitar la migración de estrategias.
"""
import pandas as pd
import pandas_ta as pta # Usamos pandas_ta como alternativa moderna a TA-Lib
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    # Configuración de Estrategia
    minimal_roi = {
        "60": 0.01, # Vender después de 60 min si profit > 1%
        "30": 0.03, # Vender después de 30 min si profit > 3%
        "0": 0.04   # Vender inmediatamente si profit > 4%
    }
    
    stoploss = -0.10 # -10% Stoploss fijo
    timeframe = '5m'
    
    # Indicadores a usar
    use_rsi = True
    use_bollinger = True

    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores técnicos y los añade al DataFrame.
        Equivalente a la fase de análisis masivo de Freqtrade.
        """
        # Ejemplo de implementación base
        if self.use_rsi:
            dataframe['rsi'] = pta.rsi(dataframe['close'], length=14)
            
        if self.use_bollinger:
            bollinger = pta.bbands(dataframe['close'], length=20, std=2)
            if bollinger is not None:
                dataframe['bb_upper'] = bollinger['BBU_20_2.0']
                dataframe['bb_middle'] = bollinger['BBM_20_2.0']
                dataframe['bb_lower'] = bollinger['BBL_20_2.0']
                
        return dataframe

    @abstractmethod
    def populate_entry_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Define las reglas de ENTRADA (Compra).
        Debe rellenar la columna 'enter_long' con 1.
        """
        return dataframe

    @abstractmethod
    def populate_exit_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Define las reglas de SALIDA (Venta).
        Debe rellenar la columna 'exit_long' con 1.
        """
        return dataframe

    def should_sell_roi(self, trade_duration_minutes: int, current_profit: float) -> bool:
        """
        Implementación del ALGORITMO ROI de Freqtrade.
        Verifica si se debe vender basado en el tiempo transcurrido y la ganancia actual.
        """
        # Ordenar lista de tiempos de ROI descendente
        roi_list = sorted([int(k) for k in self.minimal_roi.keys()], reverse=True)
        
        for duration in roi_list:
            if trade_duration_minutes >= duration:
                required_profit = self.minimal_roi[str(duration)]
                if current_profit >= required_profit:
                    return True
        return False
