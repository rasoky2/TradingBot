# 📘 Documentación Técnica del Sistema de Trading Algorítmico

**Versión:** 2.1 (ML Enhanced)
**Arquitectura:** Python Flask + Pandas/Numpy + CCXT + Scikit-Learn
**Enfoque:** Swing Trading Diario (1D)

---

## 1. Módulo de Inteligencia Artificial (ML) 🤖

El sistema incorpora un motor de predicción basado en **Random Forest Classifier** (`scikit-learn`) que opera en tiempo real.

### Función

Predecir la **Probabilidad Direccional** de la siguiente vela (Cierre Diario t+1 > Cierre Diario t).

### Arquitectura del Modelo

- **Algoritmo:** RandomForestClassifier (n_estimators=100, max_depth=5).
- **Entrenamiento:** JIT (Just-In-Time) con las últimas 500 velas.
- **Variables Predictivas (Features):**
  1.  **RSI (14):** Sobrecompra/Sobreventa.
  2.  **MACD (12, 26, 9):** Tendencia y momentum.
  3.  **MACD Histogram:** Fuerza de la tendencia.
  4.  **Bollinger Width:** Volatilidad del mercado (Squeeze detection).
  5.  **Momentum (PCT Change):** Velocidad del cambio de precio (1d y 3d).
- **Target:** Clasificación Binaria (1 = Alcista, 0 = Bajista).
- **Salida:** Probabilidad de confianza (ej. 78% Alcista).

---

## 2. Estrategia Maestra: CryptoSwing V1 👑

Es la estrategia principal diseñada para adaptarse al régimen de mercado. No utiliza una lógica única, sino que detecta el entorno y cambia su comportamiento.

### Filtro de Régimen de Mercado

El autómata clasifica el mercado en 3 estados mutuamente excluyentes:

1.  **BEAR (Bajista):**

    - _Condición:_ Precio < SMA 200.
    - _Acción:_ **PROHIBIDO COMPRAR.** El sistema entra en modo defensivo total.

2.  **TREND_UP (Tendencia Alcista Fuerte):**

    - _Condición:_ Precio > SMA 200 **Y** ADX(14) > 25.
    - _Lógica:_ Breakout Trading. Se busca comprar la fuerza.

3.  **RANGE (Lateral/Rango):**
    - _Condición:_ Precio > SMA 200 **Y** ADX(14) <= 25.
    - _Lógica:_ Mean Reversion. Se busca comprar en soportes y vender en resistencias.

### Reglas de Entrada (Señales)

- **En Tendencia (Trend Up):**
  - Entrada: Ruptura del **Donchian Channel High (20)**. (Nuevo máximo de 20 días).
- **En Rango (Range):**
  - Entrada A: **RSI(14) < 30** (Sobreventa Extrema).
  - Entrada B: Precio < **Bollinger Band Lower (20, 2.5)**.

### Reglas de Salida (Gestión de Posición)

- **Salida Técnica (Global):** Stoploss fijo de emergencia en -15%.
- **Salida Dinámica (Trend):**
  - Cierre por debajo del **Donchian Channel Low (20)**.
  - **ATR Ratchet Stop:** Chandelier Exit modificado (Máximo de 20 días - 3x ATR).
- **Salida Dinámica (Range):**
  - **RSI(14) > 70** (Sobrecompra).
  - Precio toca **Bollinger Band Upper (20, 2.5)**.

---

## 3. Estrategias Secundarias (Validación)

El sistema ejecuta en paralelo 3 estrategias clásicas para validar la señal maestra.

### A. Classic Trend (RSI + Bollinger) 📉

Estrategia de **Reversión a la Media**. Busca comprar caídas (dips) en tendencias alcistas.

- **Entrada:** RSI(14) < 35 **Y** Precio < Banda Bollinger Inferior (20, 2.0).
- **Salida:** RSI(14) > 70 **O** Precio > Banda Bollinger Superior.
- **Nivel Neutro (Donde espera comprar):** Banda Bollinger Inferior.

### B. Momentum MACD 🚀

Estrategia de **Seguimiento de Tendencia**. Busca confirmar cambios de dirección.

- **Entrada (Golden Cross):**
  - Línea MACD cruza ARRIBA de la Señal.
  - Confirmación: Cruce ocurrió en zona negativa (MACD < 0).
- **Salida (Death Cross):**
  - Línea MACD cruza ABAJO de la Señal.
- **Nivel Neutro (Donde espera comprar):** EMA 26 (Soporte dinámico) o Nivel de Breakout.
  - _Nota:_ A veces este nivel es superior al precio actual, indicando que se requiere una subida (confirmación) antes de entrar.

### C. Volatilidad Bollinger 📊

Estrategia pura de volatilidad estadística.

- **Entrada:** Precio cierra FUERA de la Banda Inferior (2 std).
- **Salida:** Precio cierra FUERA de la Banda Superior (2 std).

---

## 4. Gestión de Riesgo Global 🛡️

El "Risk Engine" del bot actúa como árbitro final:

- **Kill Switch:** Stoploss duro configurado en `config.json` (-99% para delegar, pero la estrategia usa internamente stops técnicos del 5-15%).
- **ROI (Retorno de Inversión):**
  - El sistema intenta dejar correr las ganancias (Trend Following).
  - Solo toma beneficios parciales rápidos si la señal se debilita.
- **Niveles Visuales:**
  - El dashboard muestra "ENTRADA", "STOP" y "TARGET" calculados dinámicamente según la volatilidad actual (ATR) de cada activo.
