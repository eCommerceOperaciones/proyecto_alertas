import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def clean_email_body(email_body: str) -> str:
  """
  Limpia el cuerpo del correo eliminando disclaimers y repeticiones.
  """
  # Cortar en el primer disclaimer detectado
  disclaimer_patterns = [
      "Este mensaje va dirigido",
      "This message is addressed",
      "Viewnext, S.A."
  ]
  for pattern in disclaimer_patterns:
      if pattern in email_body:
          email_body = email_body.split(pattern)[0]
          break

  # Eliminar duplicados de "Afectación" si aparecen varias veces
  lines = email_body.splitlines()
  seen_afectacion = False
  cleaned_lines = []
  for line in lines:
      if re.search(r"Afectaci[oó]:", line, re.IGNORECASE):
          if seen_afectacion:
              continue
          seen_afectacion = True
      cleaned_lines.append(line)

  return "\n".join(cleaned_lines).strip()

def extract_fecha_inicio(body: str) -> str:
  """
  Extrae la fecha de recepción desde el cuerpo del correo.
  Formato esperado: 'Recepció: dd/MM/yyyy HH:mm:ss'
  """
  match = re.search(r"Recepci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
  return match.group(1) if match else ""

def extract_fecha_resolucion(body: str) -> str:
  """
  Extrae la fecha de resolución desde el cuerpo del correo.
  Formato esperado: 'Recuperació: dd/MM/yyyy HH:mm:ss'
  """
  match = re.search(r"Recuperaci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
  return match.group(1) if match else ""

def send_slack_alert(alert_id: str, alert_name: str, alert_type: str, status: str, email_body: str, jenkins_url: str = None, ticket_url: str = None) -> bool:
  """
  Envía una alerta enriquecida a Slack usando datos reales del pipeline.
  """

  if not SLACK_WEBHOOK_URL:
      print("[WARN] SLACK_WEBHOOK_URL no configurado.")
      return False

  # Limpiar el cuerpo del correo
  email_body = clean_email_body(email_body)

  # Extraer fechas desde el body
  fecha_inicio = extract_fecha_inicio(email_body)
  fecha_resolucion = extract_fecha_resolucion(email_body)

  # Calcular duración
  duracion = "N/A"
  try:
      if fecha_inicio and fecha_resolucion:
        fmt = "%d/%m/%Y %H:%M:%S"
        start = datetime.strptime(fecha_inicio, fmt)
        end = datetime.strptime(fecha_resolucion, fmt)
        delta = end - start
        # Formato HH:mm:ss
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        duracion = f"{hours:02}:{minutes:02}:{seconds:02}"
  except Exception as e:
    print(f"[WARN] No se pudo calcular duración: {e}")

  # Criticidad y afectación
  criticidad_match = re.search(r"Criticitat:\s*([^\n/]+)", email_body, re.IGNORECASE)
  criticidad = criticidad_match.group(1).strip().capitalize() if criticidad_match else "Alta"

  afectacion_match = re.search(r"Afectaci[oó]:\s*(.+)", email_body)
  afectacion = afectacion_match.group(1).strip() if afectacion_match else "No especificada"

  # Descripción y error
  descripcion_match = re.search(r"Descripci[oó]:\s*(.+?)(?=\nError:)", email_body, re.IGNORECASE | re.DOTALL)
  descripcion = descripcion_match.group(1).strip() if descripcion_match else "No disponible"

  error_match = re.search(r"Error:\s*(.+)", email_body, re.IGNORECASE | re.DOTALL)
  error = error_match.group(1).strip() if error_match else "No especificado"

  # Color según criticidad
  color_map = {
      "Crítica": "#ff0000",
      "Alta": "#ff8000",
      "Media": "#ffcc00",
      "Baja": "#36a64f",
      "Menor": "#36a64f"
  }
  color = color_map.get(criticidad, "#36a64f")

  # Construir acciones sin elementos vacíos
  actions = []
  if jenkins_url:
      actions.append({"type": "button", "text": {"type": "plain_text", "text": "Ver en Jenkins"}, "url": jenkins_url})
  if ticket_url:
      actions.append({"type": "button", "text": {"type": "plain_text", "text": "Ver Ticket"}, "url": ticket_url})

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
                  {"type": "mrkdwn", "text": f"*Recepción:* {fecha_inicio or 'N/A'}"},
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
          }
      ]
  }

  if actions:
      payload["blocks"].append({"type": "actions", "elements": actions})

  # Depuración: imprimir payload antes de enviar
  print(json.dumps(payload, indent=2, ensure_ascii=False))

  # Enviar a Slack
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
