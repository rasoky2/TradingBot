# Flask Trading Bot

Bot de trading de criptomonedas migrado desde **Freqtrade** (FastAPI) a **Flask**.

## Características

✅ **API REST completa** con Flask
✅ **Integración con exchanges** vía CCXT (Binance, Bybit, etc.)
✅ **Dashboard web** en tiempo real
✅ **Gestión de trades** (abrir, cerrar, forzar ventas)
✅ **Sistema de estrategias** modulares
✅ **Modo Dry Run** para pruebas sin riesgo
✅ **Base de datos SQLite** con SQLAlchemy
✅ **Autenticación JWT**
✅ **WebSocket** para actualizaciones en tiempo real

## Estructura del Proyecto

```
flask-trading-bot/
├── app/
│   ├── __init__.py              # Factory de Flask
│   ├── config.py                # Configuración
│   ├── core/                    # Motor de trading
│   ├── models/                  # Modelos SQLAlchemy (Trade, Order)
│   ├── services/                # Servicios (Exchange, Data, etc.)
│   ├── strategies/              # Estrategias de trading
│   ├── routes/                  # Blueprints (API, Web)
│   ├── utils/                   # Utilidades
│   ├── static/                  # CSS, JS
│   └── templates/               # HTML templates
├── user_data/
│   ├── strategies/              # Estrategias personalizadas
│   ├── data/                    # Datos históricos
│   └── logs/                    # Logs
├── config.json                  # Configuración principal
├── requirements.txt
├── run.py                       # Entry point
└── README.md
```

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd d:\Trading\flask-trading-bot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**

```bash
.\venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar el bot

Edita `config.json` con tus credenciales del exchange:

```json
{
  "exchange": {
    "name": "binance",
    "key": "TU_API_KEY",
    "secret": "TU_API_SECRET"
  }
}
```

**IMPORTANTE:** Para pruebas, deja `"dry_run": true` activado.

## Uso

### Iniciar el bot

```bash
python run.py
```

El servidor estará disponible en: `http://127.0.0.1:5000`

### Acceder al Dashboard

Abre tu navegador en: `http://127.0.0.1:5000`

### Usar la API

#### 1. Obtener token JWT

```bash
curl -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

Respuesta:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 2. Consultar balance

```bash
curl http://127.0.0.1:5000/api/balance \
  -H "Authorization: Bearer TU_TOKEN"
```

#### 3. Ver trades

```bash
curl http://127.0.0.1:5000/api/trades \
  -H "Authorization: Bearer TU_TOKEN"
```

#### 4. Ver profit

```bash
curl http://127.0.0.1:5000/api/profit \
  -H "Authorization: Bearer TU_TOKEN"
```

## Endpoints de la API

### Públicos (sin autenticación)

- `GET /api/ping` - Health check
- `GET /api/version` - Información de versión
- `POST /api/login` - Obtener token JWT

### Protegidos (requieren JWT)

#### Información

- `GET /api/balance` - Balance de cuenta
- `GET /api/status` - Estado del bot
- `GET /api/config` - Configuración activa
- `GET /api/markets` - Mercados disponibles

#### Trades

- `GET /api/trades` - Lista de trades
- `GET /api/trades/<id>` - Trade específico
- `DELETE /api/trades/<id>` - Eliminar trade cerrado

#### Estadísticas

- `GET /api/profit` - Estadísticas de profit
- `GET /api/performance` - Performance por par

#### Datos de mercado

- `GET /api/ticker/<pair>` - Ticker de un par
- `GET /api/ohlcv/<pair>` - Datos OHLCV (velas)

#### Control

- `POST /api/start` - Iniciar bot
- `POST /api/stop` - Detener bot
- `POST /api/forcebuy` - Forzar compra
- `POST /api/forcesell` - Forzar venta

## Configuración

### config.json

```json
{
  "bot_name": "FlaskTradingBot",
  "dry_run": true,
  "stake_currency": "USDT",
  "stake_amount": 100,
  "max_open_trades": 3,

  "exchange": {
    "name": "binance",
    "key": "",
    "secret": ""
  },

  "timeframe": "5m",

  "pairlist": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],

  "stoploss": -0.1,
  "minimal_roi": {
    "0": 0.1,
    "30": 0.05,
    "60": 0.02
  },

  "strategy": "SampleStrategy"
}
```

### Parámetros principales

- **dry_run**: `true` para modo simulación, `false` para trading real
- **stake_currency**: Moneda base (USDT, BUSD, etc.)
- **stake_amount**: Cantidad a invertir por trade
- **max_open_trades**: Máximo de trades simultáneos
- **timeframe**: Intervalo de velas (1m, 5m, 15m, 1h, etc.)
- **pairlist**: Lista de pares a tradear
- **stoploss**: Stop loss en decimal (-0.10 = -10%)

## Diferencias con Freqtrade

### Eliminado

- ❌ Sistema RPC (Telegram, Discord, Webhook)
- ❌ FreqAI (Machine Learning)
- ❌ FreqUI (React frontend)
- ❌ Hyperopt avanzado
- ❌ Docker/Kubernetes configs

### Simplificado

- ✅ API: FastAPI → Flask
- ✅ WebSocket: Complejo → Socket.IO básico
- ✅ Dashboard: React → HTML/CSS/JS vanilla
- ✅ Config: YAML → JSON
- ✅ Autenticación: Sistema complejo → JWT simple

### Mantenido

- ✅ Modelos de BD (Trade, Order)
- ✅ Integración CCXT
- ✅ Sistema de estrategias
- ✅ Backtesting básico
- ✅ Gestión de órdenes

## Desarrollo

### Agregar nueva estrategia

1. Crear archivo en `app/strategies/mi_estrategia.py`
2. Heredar de `BaseStrategy`
3. Implementar métodos `populate_indicators()` y `populate_entry_trend()`
4. Actualizar `config.json` con el nombre de la estrategia

### Ejecutar migraciones

```bash
flask db init
flask db migrate -m "Descripción"
flask db upgrade
```

## Seguridad

⚠️ **IMPORTANTE:**

1. **Nunca** compartas tu `config.json` con API keys
2. Cambia el `jwt_secret_key` en producción
3. Usa HTTPS en producción
4. Implementa autenticación real (no usar admin/admin)
5. Prueba SIEMPRE en `dry_run` antes de trading real

## Soporte

- Documentación Freqtrade: https://www.freqtrade.io
- CCXT Docs: https://docs.ccxt.com
- Flask Docs: https://flask.palletsprojects.com

## Licencia

Basado en Freqtrade (GPLv3)

## Disclaimer

⚠️ **ADVERTENCIA:** Este software es solo para fines educativos. El trading de criptomonedas conlleva riesgos significativos. No arriesgues dinero que no puedas permitirte perder. Los autores no se hacen responsables de tus pérdidas.
