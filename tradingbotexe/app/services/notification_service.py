"""
Servicio de Notificaciones de Escritorio
Usa plyer para enviar alertas nativas del sistema operativo.
"""
import logging
from plyer import notification
from threading import Thread

logger = logging.getLogger(__name__)

class NotificationService:
    """Gestor de notificaciones de escritorio"""
    
    def __init__(self):
        self.last_notification_time = 0
        self.min_interval = 300 # 5 minutos mínimo entre notificaciones iguales (anti-spam)

    def send_notification(self, title: str, message: str, app_name: str = "Trading Advisor"):
        """
        Envía una notificación al sistema operativo.
        Se ejecuta en un hilo separado para no bloquear el análisis.
        """
        def _notify():
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=app_name,
                    app_icon=r"app\static\favicon.ico", 
                    timeout=10, # Segundos que se muestra
                    toast=False
                )
                logger.info(f"Notificación enviada: {title}")
            except Exception as e:
                logger.error(f"Error enviando notificación: {e}")

        # Ejecutar en background
        Thread(target=_notify).start()

    def notify_opportunity(self, pair: str, signal: str, reliability: float, price: float):
        """Helper para notificar oportunidades de trading"""
        emoji = "🚀" if signal == "COMPRA" else "🔻"
        title = f"{emoji} Oportunidad {signal}: {pair}"
        msg = (
            f"Alta Fiabilidad: {reliability}%\n"
            f"Precio: ${price:,.2f}\n"
            "Verifica el gráfico ahora."
        )
        self.send_notification(title, msg)

# Instancia global
notification_service = NotificationService()
