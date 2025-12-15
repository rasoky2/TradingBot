
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

    def prepare_data(self, df):
        """
        Feature Engineering Avanzado
        """
        data = df.copy()
        
        # --- 1. Features de Tendencia y Osciladores ---
        data['rsi'] = ta.rsi(data['close'], length=14)
        
        macd = ta.macd(data['close'])
        data['macd'] = macd['MACD_12_26_9']
        data['macdhist'] = macd['MACDh_12_26_9']
        
        adx = ta.adx(data['high'], data['low'], data['close'], length=14)
        # Manejo seguro de ADX
        if adx is not None and 'ADX_14' in adx:
            data['adx'] = adx['ADX_14']
            data['adx_slope'] = data['adx'].diff()
        else:
            data['adx'] = 0
            data['adx_slope'] = 0
            
        # --- 2. Features de Volatilidad ---
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=14)
        
        bb = ta.bbands(data['close'], length=20)
        data['bb_width'] = (bb['BBU_20_2.0'] - bb['BBL_20_2.0']) / bb['BBM_20_2.0']
        
        # --- 3. Features Relativos (Normalizados) ---
        # Distancia a SMA 50 en %
        sma50 = ta.sma(data['close'], length=50)
        data['dist_sma50'] = (data['close'] - sma50) / sma50
        
        # Volumen Relativo
        vol_sma = ta.sma(data['volume'], length=20)
        data['volume_rel'] = data['volume'] / vol_sma
        
        # --- 4. Lags (Memoria de corto plazo) ---
        # "Lo que pasó ayer y anteayer importa"
        for col in ['rsi', 'macdhist', 'volume_rel']:
            data[f'{col}_lag1'] = data[col].shift(1)
        
        # --- 5. TARGET (Lo que queremos predecir) ---
        # V2: Solo buscamos movimientos que superen 0.5 * ATR (Evitar ruido)
        # Queremos predecir la próxima vela (shift -1)
        future_close = data['close'].shift(-1)
        current_close = data['close']
        threshold = data['atr'] * 0.5 # Umbral de volatilidad mínima
        
        # Target 1: Subida Significativa
        # Target 0: Ruido o Bajada
        data['target'] = np.where(future_close > (current_close + threshold), 1, 0)
        
        data.dropna(inplace=True)
        # Limpieza de infinitos que a veces genera pandas_ta
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.dropna(inplace=True)
        return data

    def predict(self, df):
        """
        Entrena y predice la probabilidad de subida significativa.
        """
        try:
            # Necesitamos más datos para ML (mínimo histórico)
            if len(df) < 150:
                return None 
            
            full_data = self.prepare_data(df)
            
            features = [
                'rsi', 'rsi_lag1', 
                'macd', 'macdhist', 'macdhist_lag1',
                'bb_width', 
                'adx', 'adx_slope',
                'dist_sma50', 'volume_rel', 'volume_rel_lag1'
            ]
            
            # Verificar que existan las columnas
            available_features = [f for f in features if f in full_data.columns]
            
            # Split Train/Test (Test es la vela actual desconocida)
            # Entrenamos con TODO el pasado excepto la última vela (que no tiene futuro conocido aun)
            X = full_data[available_features].iloc[:-1]
            y = full_data['target'].iloc[:-1]
            
            # La vela actual para inferencia
            last_candle_features = full_data[available_features].iloc[-1:]
            
            if len(X) < 100: return None
                
            # --- 1. Calcular Accuracy usando Cross-Validation (TimeSeriesSplit) ---
            # Esto simula mejor el rendimiento en datos futuros que un simple split aleatorio
            tscv = TimeSeriesSplit(n_splits=3)
            cv_scores = cross_val_score(self.model, X, y, cv=tscv, scoring='accuracy')
            quality_score = np.mean(cv_scores)

            # --- 2. Entrenar Modelo Final con TODOS los datos ---
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
                # Neutral: La confianza es cuan cerca estamos del 50% (incertidumbre pura)
                # Opcional: mostrar complementario o 0
                confidence = (1 - abs(proba_up - 0.5) * 2) * 100 

            return {
                "direction": direction,
                "probability": round(confidence, 1), # Ahora enviamos Confianza Human-Readable
                "model_accuracy": round(quality_score * 100, 1) 
            }
            
        except Exception as e:
            print(f"Error AI prediction: {e}")
            return None
