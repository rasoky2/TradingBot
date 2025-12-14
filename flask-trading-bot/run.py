"""
Entry point para el Flask Trading Bot
"""
import logging

from app import create_app, socketio
from app.config import config

logger = logging.getLogger(__name__)

# Función principal
def main():
    """Función principal"""
    app = create_app()
    
    logger.info(f"=== {config.bot_name} ===")
    logger.info(f"Modo: {'DRY RUN' if config.dry_run else 'LIVE TRADING'}")
    logger.info(f"Exchange: {config.exchange_name}")
    logger.info(f"Estrategia: {config.strategy_name}")
    logger.info(f"Pares: {', '.join(config.pairlist)}")
    logger.info(f"API Server: http://{config.api_host}:{config.api_port}")
    logger.info("=" * 50)
    
    # Iniciar servidor
    socketio.run(
        app,
        host=config.api_host,
        port=config.api_port,
        debug=True,
        use_reloader=False
    )


if __name__ == '__main__':
    main()
