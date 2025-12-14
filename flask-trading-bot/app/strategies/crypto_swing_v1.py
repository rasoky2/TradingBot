from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class CryptoSwingV1(BaseStrategy):
    """
    Crypto Swing V1 (Long-only) — Timeframe 1D
    Estrategia de Régimen Adaptativo: Trend Following + Mean Reversion
    """
    
    # Configuración General
    timeframe = '1d'
    
    # ROI: Muy relajado, buscamos tendencias largas, dejamos correr ganancias
    # No queremos que el ROI nos saque prematuramente si la tendencia es fuerte
    minimal_roi = {
        "0": 100.0  # Desactivamos ROI por tiempo básicamente, salida por señal técnica
    }
    
    # Stoploss BASE (Risk Engine manda, pero este es el hard stop máximo)
    stoploss = -0.15 
    
    def populate_indicators(self, df):
        # --- 1. Indicadores Generales ---
        closes = df['close']
        highs = df['high']
        lows = df['low']
        
        # SMA 200 y Slope (Pendiente 10 días)
        df['sma_200'] = closes.rolling(window=200).mean()
        df['sma_200_slope'] = df['sma_200'].diff(10) # Cambio en 10 días
        
        # True Range (para ATR y ADX)
        df['tr1'] = highs - lows
        df['tr2'] = (highs - closes.shift()).abs()
        df['tr3'] = (lows - closes.shift()).abs()
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # ATR 14
        df['atr_14'] = df['tr'].rolling(window=14).mean() # Aproximación SMA para ATR
        
        # --- 2. Cálculo ADX (Manual Simplificado) ---
        plus_dm = highs.diff()
        minus_dm = lows.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        
        df['plus_di'] = 100 * (plus_dm.ewm(alpha=1/14).mean() / df['atr_14'])
        df['minus_di'] = 100 * (minus_dm.abs().ewm(alpha=1/14).mean() / df['atr_14'])
        dx = (df['plus_di'] - df['minus_di']).abs() / (df['plus_di'] + df['minus_di']) * 100
        df['adx'] = dx.rolling(window=14).mean()
        
        # --- 3. Indicadores Modulo TREND (Donchian) ---
        df['donchian_high_20'] = highs.rolling(window=20).max()
        df['donchian_low_10'] = lows.rolling(window=10).min()
        
        # Trailing Ratchet (Chandelier Exit Proxy)
        # Highest High reciente (20d) - 3 * ATR
        df['trend_atr_stop'] = df['donchian_high_20'] - (df['atr_14'] * 3.0)
        
        # --- 4. Indicadores Modulo RANGE (Bollinger) ---
        sma_20 = closes.rolling(window=20).mean()
        std_20 = closes.rolling(window=20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_mid'] = sma_20
        
        # RSI 14 (Opcional del filtro range)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # --- 5. REGIME FILTER ---
        # TREND_UP: ADX>25 y Price > SMA200 y SMA200 subiendo
        condition_trend = (
            (df['adx'] > 25) &
            (closes > df['sma_200']) &
            (df['sma_200_slope'] > 0)
        )
        df['regime'] = np.where(condition_trend, 'TREND_UP', 'RANGE')
        
        return df

    def populate_entry_trend(self, df):
        df['enter_long'] = 0
        
        # LOGICA 1: TREND MODE (Donchian Breakout)
        cond_trend_entry = (
            (df['regime'] == 'TREND_UP') &
            (df['close'] > df['donchian_high_20'].shift(1)) # Breakout ayer confirmado hoy
        )
        
        # LOGICA 2: RANGE MODE (Bollinger Mean Reversion)
        cond_range_entry = (
            (df['regime'] == 'RANGE') &
            (df['close'] < df['bb_lower']) &
            (df['rsi'] < 35) # Filtro RSI activado
        )
        
        df.loc[cond_trend_entry | cond_range_entry, 'enter_long'] = 1
        return df

    def populate_exit_trend(self, df):
        df['exit_long'] = 0
        
        # Salida TREND 1: Romper Donchian Low (Salida Técnica)
        cond_trend_exit = (
            (df['regime'] == 'TREND_UP') &
            (df['close'] < df['donchian_low_10'].shift(1))
        )
        
        # Salida TREND 2: Trailing ATR Stop (Protección Capital)
        cond_atr_exit = (
            (df['regime'] == 'TREND_UP') &
            (df['close'] < df['trend_atr_stop'].shift(1))
        )
        
        # Salida RANGE: Tocar Bollinger Mid
        cond_range_exit = (
            (df['regime'] == 'RANGE') &
            (df['close'] >= df['bb_mid'])
        )
        
        df.loc[cond_trend_exit | cond_atr_exit | cond_range_exit, 'exit_long'] = 1
        return df
