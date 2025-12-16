"""
Entry point para la Aplicación de Escritorio (Desktop)
Modo PWA/Browser para compatibilidad con Python 3.14+
"""
import logging
import threading
import time
import sys
from app import create_app, socketio
from app.config import config

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Función principal de la App de Escritorio"""
    logger.info(f"=== {config.bot_name} Desktop (Web Mode) ===")
    
    # URL inicial
    url = f"http://127.0.0.1:{config.api_port}"
    logger.info(f"Iniciando servidor en {url}")
    
    # Función para abrir el navegador/PWA automáticamente
    def open_browser():
        # Intenta abrir en modo 'app' de Chrome/Edge si es posible, sino navegador default
        try:
            # Comando para intentar abrir como app (sin barra de navegación)
            # Esto funciona si el sistema tiene asociado http/https correctamente o si detectamos chrome
            import subprocess
            # Intentar Edge o Chrome en modo app para experiencia de escritorio
            browsers = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ]
            for browser in browsers:
                import os
                if os.path.exists(browser):
                    subprocess.Popen([browser, f'--app={url}'])
                    return
            
            # Fallback a navegador por defecto
            import webbrowser
            webbrowser.open(url)
        except Exception:
            import webbrowser
            webbrowser.open(url)

    # Abrir navegador tras 1.5s
    Timer(1.5, open_browser).start()
    
    # Iniciar servidor (Bloqueante)
    # Usamos allow_unsafe_werkzeug=True si es necesario, pero async_mode='threading' ya está configurado
    try:
        app = create_app()
        socketio.run(
            app,
            host='127.0.0.1',
            port=config.api_port,
            debug=False,
            use_reloader=False 
        )
    except Exception as e:
        logger.error(f"Error fatal: {e}")

if __name__ == '__main__':
    from threading import Timer
    main()
