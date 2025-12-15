
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

class AIPredictor:
    """
    Motor de Predicción Ligero usando Random Forest.
    Entrena un modelo al vuelo con datos recientes para predecir la dirección de la proxima vela.
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100, 
            max_depth=5, 
            min_samples_leaf=5,
            max_features='sqrt',
            random_state=42
        )

    def prepare_data(self, df):
        """
        Feature Engineering: Crea variables predictivas basadas en TA.
        """
        data = df.copy()
        
        # 1. Features Técnicos (Entradas del modelo)
        # RSI
        data['rsi'] = ta.rsi(data['close'], length=14)
        
        # MACD
        macd = ta.macd(data['close'])
        data['macd'] = macd['MACD_12_26_9']
        data['macdhist'] = macd['MACDh_12_26_9']
        
        # Bollinger Width (Volatilidad)
        bb = ta.bbands(data['close'], length=20)
        data['bb_width'] = (bb['BBU_20_2.0'] - bb['BBL_20_2.0']) / bb['BBM_20_2.0']
        
        # Momentum (Cambio de precio)
        data['pct_change'] = data['close'].pct_change()
        data['pct_change_3'] = data['close'].pct_change(3) # Cambio 3 dias
        
        # 2. Target (Lo que queremos predecir)
        # Predecimos si el cierre de MAÑANA será mayor que el cierre de HOY
        data['target'] = (data['close'].shift(-1) > data['close']).astype(int)
        
        data.dropna(inplace=True)
        return data

    def predict(self, df):
        """
        Entrena y predice la probabilidad de subida para la vela actual (última).
        """
        try:
            if len(df) < 100:
                return None # Datos insuficientes
            
            # Preparar datos
            full_data = self.prepare_data(df)
            
            # Separar datos pasados (entrenamiento) de la vela actual (predicción)
            # La vela actual NO tiene target (no sabemos el futuro), pero si tiene features
            # Usamos todas las velas MENOS la última para entrenar
            X = full_data[['rsi', 'macd', 'macdhist', 'bb_width', 'pct_change', 'pct_change_3']].iloc[:-1]
            y = full_data['target'].iloc[:-1]
            
            # La vela actual para predecir (features de hoy)
            last_candle_features = full_data[['rsi', 'macd', 'macdhist', 'bb_width', 'pct_change', 'pct_change_3']].iloc[-1:]
            
            if len(X) < 50:
                return None
                
            # Entrenar (Training al vuelo)
            self.model.fit(X, y)
            
            # Predecir Probabilidad (Clase 1 = Subida)
            proba = self.model.predict_proba(last_candle_features)[0][1]
            
            # Score de Confianza (Feature Importance opcional)
            
            direction = "ALCISTA" if proba > 0.5 else "BAJISTA"
            confidence = proba * 100 if proba > 0.5 else (1 - proba) * 100
            
            return {
                "direction": direction,
                "probability": round(confidence, 1),
                "raw_score": round(proba, 4)
            }
            
        except Exception as e:
            print(f"Error AI prediction: {e}")
            return None
