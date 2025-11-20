import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def extract_fecha_resolucion(body):
  match = re.search(r"Recuperació:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
  return match.group(1) if match else ""

def send_slack_alert(alert_id, alert_name, alert_type, status, email_body, jenkins_url=None, ticket_url=None):
  """
  Envía una alerta enriquecida a Slack usando datos reales del pipeline.
  """

  if not SLACK_WEBHOOK_URL:
      print("[WARN] SLACK_WEBHOOK_URL no configurado.")
      return False

  # Extraer datos clave
  fecha_recepcion = alert_id  # Si ALERT_ID es fecha, usar directamente
  fecha_resolucion = extract_fecha_resolucion(email_body)

  # Calcular duración
  duracion = "N/A"
  try:
      if fecha_recepcion and fecha_resolucion:
          fmt = "%d/%m/%Y %H:%M:%S"
          start = datetime.strptime(fecha_recepcion, fmt)
          end = datetime.strptime(fecha_resolucion, fmt)
          duracion = f"{int((end - start).total_seconds() / 60)} min"
  except Exception:
      pass

  # Criticidad y afectación
  criticidad = "Crítica" if "Crítica" in email_body else "Alta"
  afectacion = re.search(r"Afectació:\s*(.+)", email_body)
  afectacion = afectacion.group(1) if afectacion else "No especificada"

  # Descripción y error
  descripcion = re.search(r"Descripció:\s*(.+)", email_body)
  descripcion = descripcion.group(1) if descripcion else "No disponible"
  error = re.search(r"Error:\s*(.+)", email_body)
  error = error.group(1) if error else "No especificado"

  # Color según criticidad
  color_map = {
      "Crítica": "#ff0000",
      "Alta": "#ff8000",
      "Media": "#ffcc00",
      "Baja": "#36a64f"
  }
  color = color_map.get(criticidad, "#36a64f")

  # Payload enriquecido
  payload = {
      "blocks": [
          {
              "type": "header",
              "text": {"type": "plain_text", "text": f"🚨 {criticidad} - {alert_name}", "emoji": True}
          },
          {
              "type": "section",
              "fields": [
                  {"type": "mrkdwn", "text": f"*Estado:* {status}"},
                  {"type": "mrkdwn", "text": f"*Tipo:* {alert_type}"},
                  {"type": "mrkdwn", "text": f"*ID:* {alert_id}"},
                  {"type": "mrkdwn", "text": f"*Duración:* {duracion}"}
              ]
          },
          {
              "type": "section",
              "fields": [
                  {"type": "mrkdwn", "text": f"*Recepción:* {fecha_recepcion}"},
                  {"type": "mrkdwn", "text": f"*Recuperación:* {fecha_resolucion or 'N/A'}"}
              ]
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Descripción:*\n{descripcion}"}
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Error:*\n{error}"}
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Afectación:*\n{afectacion}"}
          },
          {
              "type": "actions",
              "elements": [
                  {"type": "button", "text": {"type": "plain_text", "text": "Ver en Jenkins"}, "url": jenkins_url} if jenkins_url else {},
                  {"type": "button", "text": {"type": "plain_text", "text": "Ver Ticket"}, "url": ticket_url} if ticket_url else {}
              ]
          }
      ]
  }

  try:
      resp = requests.post(SLACK_WEBHOOK_URL, json=payload)
      if resp.status_code == 200:
          print("[INFO] Mensaje enriquecido enviado a Slack.")
          return True
      else:
          print(f"[ERROR] Fallo al enviar mensaje: {resp.status_code} - {resp.text}")
          return False
  except Exception as e:
      print(f"[ERROR] Excepción enviando mensaje: {e}")
      return False
