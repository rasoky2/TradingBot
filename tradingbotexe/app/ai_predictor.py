
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score, TimeSeriesSplit

class AIPredictor:
    """
    Motor de Predicción V3 (Turbo) usando HistGradientBoosting.
    Más rápido y preciso que Random Forest para detectar patrones sutiles.
    """
    
    def __init__(self):
        # Motor Nuevo: Gradient Boosting (LigthGBM inspired)
        self.model = HistGradientBoostingClassifier(
            learning_rate=0.05,        # Aprendizaje más fino
            max_iter=200,              # Más iteraciones (árboles)
            max_depth=5,               # Profundidad controlada para evitar overfitting
            l2_regularization=1.0,     # Regularización para generalizar mejor
            early_stopping=True,       # Parar si deja de mejorar
            random_state=42
        )

    def prepare_data(self, df, df_macro=None):
        """
        Feature Engineering Avanzado con Multi-Timeframe (Micro + Macro)
        """
        data = df.copy()
        
        # --- 1. Features Micro (5m) ---
        data['rsi'] = ta.rsi(data['close'], length=14)
        
        macd = ta.macd(data['close'])
        data['macd'] = macd['MACD_12_26_9']
        data['macdhist'] = macd['MACDh_12_26_9']
        
        adx = ta.adx(data['high'], data['low'], data['close'], length=14)
        if adx is not None and 'ADX_14' in adx:
            data['adx'] = adx['ADX_14']
            data['adx_slope'] = data['adx'].diff()
        else:
            data['adx'] = 0
            data['adx_slope'] = 0
            
        # Volatilidad
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=14)
        bb = ta.bbands(data['close'], length=20)
        data['bb_width'] = (bb['BBU_20_2.0'] - bb['BBL_20_2.0']) / bb['BBM_20_2.0']
        
        # Relativos
        sma50 = ta.sma(data['close'], length=50)
        data['dist_sma50'] = (data['close'] - sma50) / sma50
        
        vol_sma = ta.sma(data['volume'], length=20)
        data['volume_rel'] = data['volume'] / vol_sma
        
        # --- 2. Features MACRO (4H) - "La Visión General" ---
        if df_macro is not None and not df_macro.empty:
            # Calculamos indicadores en el DF Macro
            macro = df_macro.copy()
            macro['rsi_macro'] = ta.rsi(macro['close'], length=14)
            macro['sma200_macro'] = ta.sma(macro['close'], length=200)
            
            # Tendencia Macro: Precio vs SMA200 (1=Alcista, -1=Bajista)
            macro['trend_macro'] = np.where(macro['close'] > macro['sma200_macro'], 1, -1)
            
            # Seleccionamos solo columnas útiles y renombramos
            macro_feats = macro[['timestamp', 'rsi_macro', 'trend_macro']].copy()
            
            # MERGE INTELIGENTE:
            # Unimos por timestamp "hacia atrás" (cada vela de 5m hereda el estado de la vela de 4h que la contiene)
            # pandas.merge_asof es perfecto para esto
            data = data.sort_values('timestamp')
            macro_feats = macro_feats.sort_values('timestamp')
            
            data = pd.merge_asof(data, macro_feats, on='timestamp', direction='backward')
            
            # Rellenar nulos iniciales (si el macro empieza despues)
            data['rsi_macro'].fillna(50, inplace=True)
            data['trend_macro'].fillna(0, inplace=True)
        else:
            # Fallback si no hay macro
            data['rsi_macro'] = 50
            data['trend_macro'] = 0

        # --- 3. Lags (Memoria de corto plazo) ---
        for col in ['rsi', 'macdhist', 'volume_rel']:
            data[f'{col}_lag1'] = data[col].shift(1)
        
        # --- 4. TARGET (Predicción) ---
        future_close = data['close'].shift(-1)
        current_close = data['close']
        threshold = data['atr'] * 0.5 
        
        data['target'] = np.where(future_close > (current_close + threshold), 1, 0)
        
        data.dropna(inplace=True)
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.dropna(inplace=True)
        return data

    def predict(self, df, df_macro=None):
        """
        Entrena y predice la probabilidad de subida significativa.
        Ahora soporta contexto MACRO (4H).
        """
        try:
            # Necesitamos más datos para ML (mínimo histórico)
            if len(df) < 150:
                print("Insuficientes datos para ML")
                return None 
            
            # Feature Engineering con Macro
            full_data = self.prepare_data(df, df_macro)
            
            features = [
                'rsi', 'rsi_lag1', 
                'macd', 'macdhist', 'macdhist_lag1',
                'bb_width', 
                'adx', 'adx_slope',
                'dist_sma50', 'volume_rel', 'volume_rel_lag1',
                # New Macro Features
                'rsi_macro', 'trend_macro'
            ]
            
            # Verificar disponibilidad
            available_features = [f for f in features if f in full_data.columns]
            
            # Split Train/Test
            X = full_data[available_features].iloc[:-1]
            y = full_data['target'].iloc[:-1]
            last_candle_features = full_data[available_features].iloc[-1:]
            
            if len(X) < 100: return None
                
            # Cross-Validation Score
            tscv = TimeSeriesSplit(n_splits=3)
            cv_scores = cross_val_score(self.model, X, y, cv=tscv, scoring='accuracy')
            quality_score = np.mean(cv_scores)

            # Entrenar Final
            self.model.fit(X, y)
            
            # Predecir
            proba_up = self.model.predict_proba(last_candle_features)[0][1]
            
            # Lógica de Decisión V2
            direction = "NEUTRAL"
            confidence = 0.0
            
            if proba_up > 0.55: 
                direction = "ALCISTA"
                confidence = proba_up * 100
            elif proba_up < 0.45: 
                direction = "BAJISTA"
                confidence = (1 - proba_up) * 100
            else:
                confidence = (1 - abs(proba_up - 0.5) * 2) * 100 
                # Si estamos neutral pero la tendencia macro es clara, usamos sesgo macro
                if confidence < 20: # Muy baja confianza
                   current_macro_trend = last_candle_features['trend_macro'].iloc[0]
                   if current_macro_trend == 1: direction = "ALCISTA (Macro)"
                   elif current_macro_trend == -1: direction = "BAJISTA (Macro)"

            return {
                "direction": direction,
                "probability": round(confidence, 1), 
                "model_accuracy": round(quality_score * 100, 1) 
            }
            
        except Exception as e:
            print(f"Error AI prediction: {e}")
            import traceback
            traceback.print_exc()
            return None

