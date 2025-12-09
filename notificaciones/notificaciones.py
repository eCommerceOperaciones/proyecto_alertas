import os
from loguru import logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Leer configuración desde variables de entorno
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

def enviar_correo_html(destinatario, asunto, html_contenido):
    """Envía un correo HTML usando SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = EMAIL_USER
        msg["To"] = destinatario

        parte_html = MIMEText(html_contenido, "html")
        msg.attach(parte_html)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, destinatario, msg.as_string())

        logger.info(f"Correo enviado a {destinatario}")
    except Exception as e:
        logger.error(f"Error enviando correo: {e}")
        raise

def enviar_a_slack(mensaje):
    """Envía un mensaje a un canal de Slack usando el Channel ID."""
    if not SLACK_TOKEN or not SLACK_CHANNEL_ID:
        logger.error("SLACK_TOKEN o SLACK_CHANNEL_ID no configurados.")
        return

    client = WebClient(token=SLACK_TOKEN)
    try:
        client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=mensaje)
        logger.info(f"Mensaje enviado a Slack canal {SLACK_CHANNEL_ID}")
    except SlackApiError as e:
        logger.error(f"Error enviando a Slack: {e.response['error']}")
        raise

if __name__ == "__main__":
    logger.info("Iniciando notificaciones...")

    # Ejemplo de uso: estos valores vendrán del pipeline
    enviar_correo_html(
        destinatario="destinatario@ejemplo.com",
        asunto="Alerta Real Detectada",
        html_contenido="<h1>Se ha detectado una alerta real</h1>"
    )

    enviar_a_slack("Se ha enviado un correo al cliente por alerta real.")
