from .base_strategy import BaseStrategy
import pandas as pd
import pandas_ta as ta
import numpy as np

class CryptoSwingV1(BaseStrategy):
    """
    Crypto Swing V1 (Long-only) — Timeframe 1D
    Estrategia de Régimen Adaptativo: Trend, Range & Bear Defense
    """
    
    # Configuración General
    timeframe = '1d'
    
    # ROI: Desactivado (100%), salida controlada por señal técnica
    minimal_roi = { "0": 100.0 }
    
    # Kill Switch Global (Stoploss de emergencia)
    stoploss = -0.99 
    
    def populate_indicators(self, df):
        # --- 1. Indicadores Generales (Pandas TA) ---
        closes = df['close']
        highs = df['high']
        lows = df['low']
        
        # SMA 200 y Slope
        df['sma_200'] = ta.sma(closes, length=200)
        # Calculamos slope manualmente porque ta.slope a veces varía en implementación
        df['sma_200_slope'] = df['sma_200'].diff(10)
        
        # ATR 14 (Standard Wilder)
        df['atr_14'] = ta.atr(highs, lows, closes, length=14)
        
        # ADX 14 (Standard Wilder)
        # pandas_ta devuelve un DF con ADX_14, DMP_14, DMN_14
        adx_df = ta.adx(highs, lows, closes, length=14)
        df['adx'] = adx_df['ADX_14']
        
        # --- 2. Indicadores Modulo TREND (Donchian) ---
        df['donchian_high_20'] = highs.rolling(window=20).max()
        df['donchian_low_10'] = lows.rolling(window=10).min()
        
        # Trailing Ratchet (Chandelier Exit Proxy)
        # Highest High reciente (20d) - 3 * ATR
        # Nota: En sistemas 'Real Money', usaríamos un acumulador trade-aware.
        df['trend_atr_stop'] = df['donchian_high_20'] - (df['atr_14'] * 3.0)
        
        # --- 3. Indicadores Modulo RANGE (Bollinger & RSI) ---
        # Bollinger Bands (20, 2.0)
        bb = ta.bbands(closes, length=20, std=2.0)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        df['bb_mid'] = bb['BBM_20_2.0']
        
        # RSI 14
        df['rsi'] = ta.rsi(closes, length=14)
        
        # --- 4. REGIME FILTER (3 Estados) ---
        # Estado 1: TREND_UP (Alcista Fuerte)
        # ADX>25, Precio > SMA200, SMA subiendo
        cond_trend = (
            (df['adx'] > 25) &
            (closes > df['sma_200']) &
            (df['sma_200_slope'] > 0)
        )
        
        # Estado 2: RANGE (Indeciso pero Seguro)
        # No es tendencia fuerte, pero estamos SOBRE la SMA200 (Bullish bias)
        cond_range = (
            (closes > df['sma_200']) &
            (~cond_trend)
        )
        
        # Estado 3: BEAR (Bajista / Peligro) - Default
        # Debajo de SMA200 -> PROHIBIDO OPERAR LONG
        
        df['regime'] = 'BEAR'
        df.loc[cond_range, 'regime'] = 'RANGE'
        df.loc[cond_trend, 'regime'] = 'TREND_UP'
        
        return df

    def populate_entry_trend(self, df):
        df['enter_long'] = 0
        
        # LOGICA 1: TREND MODE (Donchian Breakout)
        cond_trend_entry = (
            (df['regime'] == 'TREND_UP') &
            (df['close'] > df['donchian_high_20'].shift(1)) # Breakout confirmado
        )
        
        # LOGICA 2: RANGE MODE (Bollinger Mean Reversion)
        # Solo entramos en rango si estamos sobre SMA200 (Regime=RANGE garantiza esto)
        cond_range_entry = (
            (df['regime'] == 'RANGE') &
            (df['close'] < df['bb_lower']) &
            (df['rsi'] < 35)
        )
        
        # NOTA: En BEAR no hay entradas.
        
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
