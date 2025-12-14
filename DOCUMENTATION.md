# 📘 Documentación Técnica Avanzada: Flask Trading Bot

Este documento sirve como referencia exhaustiva para la arquitectura, lógica de trading y matemáticas subyacentes del sistema. Se detallan las 4 estrategias activas y sus condiciones exactas.

---

## 🏛️ Arquitectura del Sistema

El sistema opera bajo un modelo de **Monolito Modular** diseñado para el análisis técnico en tiempo real en el timeframe Diario (1D).

### Flujo de Datos

1.  **Ingesta**: Descarga de velas OHLCV desde Binance mediante `ccxt`.
2.  **Cálculo**: Procesamiento vectorizado con `pandas` para generar indicadores.
3.  **Ejecución**: Evaluación paralela de 4 estrategias independientes.
4.  **Visualización**: Dashboard con gráficos interactivos (`Lightweight Charts`) y conexión WebSocket.

---

## 🧠 Estrategia 1: CryptoSwing V1 (Master)

_Archivo: `app/strategies/crypto_swing_v1.py`_

Esta es la estrategia principal, diseñada con lógica de **Cambio de Régimen (Regime Switching)**. Adapta su comportamiento según si el mercado está en Tendencia o en Rango.

### A. Filtro de Régimen (El Cerebro)

El bot decide primero el estado del mercado:

- **Modo TREND_UP (Tendencia Alcista)**:
  - ADX (14) > 25 (Tendencia Fuerte)
  - Precio > SMA (200) (Tendencia Secular Alcista)
  - Pendiente SMA (200) > 0 (Tendencia Acelerando)
- **Modo RANGE (Rango/Lateral)**:
  - Cualquier estado que no cumpla todas las condiciones anteriores.

### B. Lógica de Entrada

- **En TREND_UP (Breakout)**:
  - Condición: Precio de Cierre > Canal Donchian Superior (20 días, desplazado 1 día).
  - Filosofía: Comprar fortaleza en nuevos máximos.
- **En RANGE (Mean Reversion)**:
  - Condición: (Precio < Banda Bollinger Inferior) **Y** (RSI < 35).
  - Filosofía: Comprar barato con sobreventa confirmada.

### C. Lógica de Salida

- **Trend Exit**: Precio rompe el Canal Donchian Inferior (10 días).
- **Range Exit**: Precio toca la Banda Bollinger Media (SMA 20).
- **Stop Loss Catastrófico (ATR Ratchet)**:
  - Nivel: Máximo de 20 días - (3.0 \* ATR 14).
  - Acción: Si el precio cierra por debajo, venta inmediata.

---

## 📈 Estrategia 2: Classic Trend (RSI + Bollinger)

_Archivo: `app/strategies/trend_strategy.py`_

A pesar de su nombre, es una estrategia clásica de **"Buy the Dip" (Comprar la Caída)** en tendencias alcistas profundas.

### Indicadores Base

- **RSI (Relative Strength Index)**: Periodo 14.
- **Bollinger Bands**: Periodo 20, Desviación Estándar 2.0.

### Fórmula de Entrada

Busca condiciones extremas de sobreventa:

- **Condición**: (RSI < 35) **Y** (Precio <= Banda Bollinger Inferior).

### Fórmula de Salida

Busca condiciones de sobrecompra o recuperación total:

- **Condición**: (RSI > 70) **O** (Precio >= Banda Bollinger Superior).

---

## 🚀 Estrategia 3: Momentum MACD

_Archivo: `app/strategies/macd_strategy.py`_

Estrategia de **Seguimiento de Tendencia (Trend Following)** basada en el momentum puro del precio. Busca capturar el inicio de grandes movimientos.

### Indicadores Base

- **MACD Line**: EMA(12) - EMA(26).
- **Signal Line**: EMA(9) de la línea MACD.
- **Histograma**: MACD - Signal.

### Fórmula de Entrada (Golden Cross)

Busca el cruce alcista, pero solo cuando el activo está "barato" (bajo cero).

- **Condición**:
  1.  MACD > Signal (Cruce actual).
  2.  MACD[Ayer] <= Signal[Ayer] (Confirmación de cruce).
  3.  MACD < 0 (El cruce ocurre en zona negativa/recuperación).

### Fórmula de Salida (Death Cross)

- **Condición**: MACD < Signal (Cruce bajista confirmado).

---

## � Estrategia 4: Volatilidad Bollinger

_Archivo: `app/strategies/bollinger_strategy.py`_

Estrategia pura de **Reversión a la Media (Mean Reversion)** basada en la volatilidad estadística. Asume que el precio siempre vuelve a su promedio.

### Indicadores Base

- **Bollinger Bands**: SMA de 20 periodos +/- 2 Desviaciones Estándar.

### Fórmula de Entrada

- **Condición**: Precio < Banda Bollinger Inferior.
  - Significado: El precio está estadísticamente "barato" (fuera del 95% de probabilidad normal).

### Fórmula de Salida

- **Condición**: Precio > Banda Bollinger Superior.
  - Significado: El precio está estadísticamente "caro".

---

## 🛡️ Gestión de Riesgo Global

El sistema aplica capas de seguridad transversales a todas las estrategias:

### 1. Kill Switch

- **Configuración**: `stoploss: -0.99`.
- **Función**: Desactiva el stop loss fijo porcentual para dar control total a la lógica algorítmica.

### 2. Validación de Señales (Lookahead Bias)

Todas las estrategias utilizan `.shift(1)` o comparan el cierre de la vela actual confirmada. Nunca se opera "adivinando" el cierre de una vela en formación.

### 3. Fiabilidad Normalizada (Score 0-100%)

Para asistir la decisión humana, se calcula un score matemático:

- **MACD**: Compara el histograma actual contra el máximo de los últimos 20 días.
- **RSI**: Penaliza la fiabilidad si el RSI está en zona neutra (40-60).
- **Tendencia**: Premia el ADX alto (>25).

---

**Versión del Documento**: 2.0 (Full Detail - No Tables)
**Fecha**: Diciembre 2025
