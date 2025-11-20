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
  if "Este mensaje va dirigido" in email_body:
      email_body = email_body.split("Este mensaje va dirigido")[0]
  return email_body.strip()

def parse_email_body(email_body: str) -> dict:
  """
  Extrae todos los campos relevantes del cuerpo del correo.
  """
  email_body = clean_email_body(email_body)
  data = {}

  criticidad_match = re.search(r"Criticitat:\s*([^\n/]+)", email_body, re.IGNORECASE)
  data["criticidad"] = criticidad_match.group(1).strip().capitalize() if criticidad_match else "No especificada"

  estado_match = re.search(r"Estat:\s*([^\n]+)", email_body, re.IGNORECASE)
  data["estado"] = estado_match.group(1).strip() if estado_match else "No especificado"

  recepcion_match = re.search(r"Recepci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", email_body)
  data["recepcion"] = recepcion_match.group(1) if recepcion_match else None

  recuperacion_match = re.search(r"Recuperaci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", email_body)
  data["recuperacion"] = recuperacion_match.group(1) if recuperacion_match else None

  durada_match = re.search(r"Durada:\s*([^\n]+)", email_body, re.IGNORECASE)
  data["durada"] = durada_match.group(1).strip() if durada_match else None

  descripcion_match = re.search(r"Descripci[oó]:\s*(.+?)(?=\nError:)", email_body, re.IGNORECASE | re.DOTALL)
  data["descripcion"] = descripcion_match.group(1).strip() if descripcion_match else "No disponible"

  error_match = re.search(r"Error:\s*(.+)", email_body, re.IGNORECASE | re.DOTALL)
  data["error"] = error_match.group(1).strip() if error_match else "No especificado"

  afectacion_match = re.search(r"Afectaci[oó]:\s*(.+)", email_body, re.IGNORECASE)
  data["afectacion"] = afectacion_match.group(1).strip() if afectacion_match else "No especificada"

  if data["recepcion"] and data["recuperacion"]:
      try:
          fmt = "%d/%m/%Y %H:%M:%S"
          start = datetime.strptime(data["recepcion"], fmt)
          end = datetime.strptime(data["recuperacion"], fmt)
          data["duracion_calc"] = f"{int((end - start).total_seconds() / 60)} min"
      except Exception as e:
          print(f"[WARN] No se pudo calcular duración: {e}")
          data["duracion_calc"] = "N/A"
  else:
      data["duracion_calc"] = data["durada"] or "N/A"

  return data

def send_slack_alert_from_body(alert_id: str, alert_name: str, alert_type: str, email_body: str, jenkins_url: str = None, ticket_url: str = None):
  """
  Envía alerta a Slack extrayendo todos los datos del body, pero manteniendo el alert_id como identificador.
  """
  if not SLACK_WEBHOOK_URL:
      print("[WARN] SLACK_WEBHOOK_URL no configurado.")
      return False

  data = parse_email_body(email_body)

  color_map = {
      "Crítica": "#ff0000",
      "Alta": "#ff8000",
      "Media": "#ffcc00",
      "Baja": "#36a64f",
      "Menor": "#36a64f"
  }
  color = color_map.get(data["criticidad"], "#36a64f")

  actions = []
  if jenkins_url:
      actions.append({"type": "button", "text": {"type": "plain_text", "text": "Ver en Jenkins"}, "url": jenkins_url})
  if ticket_url:
      actions.append({"type": "button", "text": {"type": "plain_text", "text": "Ver Ticket"}, "url": ticket_url})

  payload = {
      "blocks": [
          {
              "type": "header",
              "text": {"type": "plain_text", "text": f"🚨 {data['criticidad']} - {alert_name}", "emoji": True}
          },
          {
              "type": "section",
              "fields": [
                  {"type": "mrkdwn", "text": f"*Estado:* {data['estado']}"},
                  {"type": "mrkdwn", "text": f"*Tipo:* {alert_type}"},
                  {"type": "mrkdwn", "text": f"*ID:* {alert_id}"},
                  {"type": "mrkdwn", "text": f"*Duración:* {data['duracion_calc']}"}
              ]
          },
          {
              "type": "section",
              "fields": [
                  {"type": "mrkdwn", "text": f"*Recepción:* {data['recepcion'] or 'N/A'}"},
                  {"type": "mrkdwn", "text": f"*Recuperación:* {data['recuperacion'] or 'N/A'}"}
              ]
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Descripción:*\n{data['descripcion']}"}
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Error:*\n{data['error']}"}
          },
          {
              "type": "section",
              "text": {"type": "mrkdwn", "text": f"*Afectación:*\n{data['afectacion']}"}
          }
      ]
  }

  if actions:
      payload["blocks"].append({"type": "actions", "elements": actions})

  print(json.dumps(payload, indent=2, ensure_ascii=False))

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
