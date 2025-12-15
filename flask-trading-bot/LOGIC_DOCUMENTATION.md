# 📘 Flask Trading Bot (v1.0) - Documentación Técnica

Esta guía explica la lógica interna, los algoritmos y el flujo de decisión del bot.

---

## 🧠 1. El Cerebro Predictivo (Machine Learning)

El bot no usa modelos pre-entrenados estáticos. Utiliza un sistema de **Adaptive Just-In-Time Learning**: se entrena desde cero cada vez que solicitas un análisis.

### Flujo de Predicción (`ai_predictor.py`)

1. **Ingesta de Datos**:

   - Descarga las últimas **500 velas** (Timeframe 1D) del exchange.
   - Esto cubre aprox. 1.5 años de historia de mercado para capturar diferentes regímenes (Bull/Bear/Rango).

2. **Ingeniería de Características (Features)**:
   El bot transforma el precio crudo en **dimensionales** comprensibles para la IA:

   - **Tendencia**: RSI, MACD, ADX.
   - **Volatilidad**: Ancho de Bandas de Bollinger, ATR.
   - **Momentum**: Distancia a SMA 50.
   - **Memoria**: Lags (¿Cómo estaba el RSI ayer?).

3. **Definición del Target (Objetivo)**:

   - No predice simplemente "Subir/Bajar".
   - **Target Real**: `Cierre Futuro > Cierre Actual + (0.5 * ATR)`
   - _Traducción_: Solo clasifica como "ALCISTA" si el movimiento proyectado supera el ruido del mercado.

4. **Algoritmo & Validación**:
   - **Modelo**: Random Forest Classifier (200 árboles).
   - **Validación OOB (Out-of-Bag)**: Usa datos no vistos durante el entrenamiento para autoevaluarse.

### Interpretación del Dashboard

- **Probabilidad**: ¿Qué tan seguro está el modelo de que subirá/bajará hoy?
- **Historial Acc (Accuracy)**: ¿Qué tan bueno ha sido este modelo prediciendo los últimos 500 días? (Si es <55%, es mejor ignorarlo).

---

## 🛡️ 2. El "Dream Team" de Estrategias

El bot no depende de una sola lógica. Ejecuta **6 estrategias en paralelo** y busca consenso.

| Estrategia            | Tipo        | Filosofía                                                            | Gatillo de Compra                                            |
| :-------------------- | :---------- | :------------------------------------------------------------------- | :----------------------------------------------------------- |
| **CryptoSwing V1**    | Híbrida     | **Adaptativa**. Detecta si hay tendencia o rango y cambia su lógica. | Breakout de Donchian (Tendencia) o Rebote Bollinger (Rango). |
| **Turtle Soup** 🐢    | Smart Money | **Caza-stops**. Busca falsas rupturas de mínimos.                    | Precio rompe mínimo de 20 días pero cierra arriba (Reclaim). |
| **RSI Divergence** 📉 | Reversal    | **Contrarian**. Busca agotamiento de vendedores.                     | Precio baja, pero RSI sube (Divergencia Alcista).            |
| **MACD Trend** 🌊     | Momentum    | **Lento/Seguro**. Sigue olas grandes.                                | Cruce de Oro MACD bajo cero.                                 |
| **Bollinger** 🎯      | Mean Rev.   | **Rebote**. Compra barato.                                           | Precio cae de banda baja + Vela Verde de confirmación.       |
| **Classic Trend** 📈  | Trend       | **Estándar**.                                                        | RSI < 35 + Toque de banda inferior.                          |

---

## 📊 3. Cálculo de Fiabilidad (Score de Confianza)

Cada señal recibe una puntuación del 0 al 100% llamada `Reliability`. No es aleatoria, es un cálculo multifactorial:

- **Base**: 50 puntos (Neutral).
- **Bonus por Trend**: Si ADX > 25 (Tendencia Fuerte), suma puntos.
- **Bonus por Extremos**: Si RSI < 30 (Sobreventa), suma puntos.
- **Bonus por Estructura**: Si el precio está en soporte de Bollinger, suma puntos.
- **Bonus por Señal Activa**: Si la estrategia dice "COMPRA", suma +15 puntos automáticamente.

---

## ⚙️ 4. Gestión de Riesgo

El bot prioriza **no perder dinero** sobre ganar mucho.

1. **Protección Macro (The Bear Defense)**:

   - Si el precio está **debajo de la SMA 200** (Tendencia bajista de largo plazo), la estrategia principal (`Swing V1`) entra en modo `BEAR` y **prohíbe compras** de tendencia. Solo permite operar rebotes muy específicos.

2. **Salidas Dinámicas**:
   - No usa un objetivo de precio fijo.
   - Usa **Trailing ATR**: El stop-loss persigue al precio a una distancia segura. Si el precio se da la vuelta, cierra la operación asegurando ganancias.

---

## 📂 Estructura de Archivos Clave

- `app/services/analysis_service.py`: **El Director**. Orquesta todas las estrategias.
- `app/ai_predictor.py`: **El Matemático**. Ejecuta el Machine Learning.
- `config.json`: **El Panel de Control**. Define pares, capital y timeframes.
