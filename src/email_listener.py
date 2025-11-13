import os
import re
import requests
import logging
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from datetime import datetime

# ============================
# Configuración de logging
# ============================
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  datefmt="%Y-%m-%d %H:%M:%S"
)

# ============================
# Cargar variables de entorno
# ============================
load_dotenv()

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Jenkins
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_Alertas_Pruebas")

# Alertas configuradas
ALERTS = {
  "Alerta Acces Frontal": {
      "from": "rpinheiro@viewnext.com",
      "subject_contains": "ELS MEUS DOCUMENTS",
      "body_contains": "ACCES_FRONTAL_EMD",
      "script": "acces_frontal_emd"
  },
  "Alerta Frameworks": {
      "from": "rpinheiro@viewnext.com",
      "subject_contains": "FRAMEWORKS EFORMULARIS",
      "body_contains": "01_CARREGA_URL_WEFOSJX26",
      "script": "01_carrega_url_wsdl"
  }
}

def decode_mime_words(s):
  try:
      return str(make_header(decode_header(s)))
  except:
      return s

def normalize_text(text):
  if not isinstance(text, str):
      return ""
  return re.sub(r"\s+", " ", text.strip().lower())

def parse_email_body(email_message):
  body = ""
  if email_message.is_multipart():
      for part in email_message.walk():
          content_type = part.get_content_type()
          if content_type in ("text/plain", "text/html"):
              payload = part.get_payload(decode=True)
              if not payload:
                  continue
              body = payload.decode(errors="ignore")
              if content_type == "text/html":
                  body = BeautifulSoup(body, "html.parser").get_text()
              break
  else:
      payload = email_message.get_payload(decode=True)
      if payload:
          body = payload.decode(errors="ignore")
  return body

def extract_alert_id(body):
  # Buscar patrón Recepció: dd/mm/yyyy HH:MM:SS
  match = re.search(r"Recepci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
  if match:
      fecha_hora = match.group(1)
      try:
          dt = datetime.strptime(fecha_hora, "%d/%m/%Y %H:%M:%S")
          return dt.strftime("%Y%m%d_%H%M%S")
      except ValueError:
          logging.error(f"Formato de fecha/hora inválido en Recepció: {fecha_hora}")
          return None
  logging.error("No se encontró campo 'Recepció:' en el correo")
  return None

def detect_alert(from_email, subject, body):
  from_norm = normalize_text(from_email)
  subject_norm = normalize_text(subject)
  body_norm = normalize_text(body)

  activa_pattern = re.compile(r"alerta\s*activa", re.IGNORECASE)
  resuelta_pattern = re.compile(r"alerta\s*resuelta", re.IGNORECASE)

  alert_type = None
  if activa_pattern.search(subject_norm) or activa_pattern.search(body_norm):
      alert_type = "ACTIVA"
  elif resuelta_pattern.search(subject_norm) or resuelta_pattern.search(body_norm):
      alert_type = "RESUELTA"

  alert_id = extract_alert_id(body)
  if not alert_id:
      return None, None, alert_type, None  # Error técnico si no hay ID

  for alert_name, data in ALERTS.items():
      match = True
      if "from" in data and normalize_text(data["from"]) not in from_norm:
          match = False
      if "subject_contains" in data and normalize_text(data["subject_contains"]) not in subject_norm:
          match = False
      if "body_contains" in data and normalize_text(data["body_contains"]) not in body_norm:
          match = False
      if match:
          logging.info(f"✅ Alerta detectada: {alert_name} | Tipo: {alert_type} | ID: {alert_id}")
          return alert_name, data["script"], alert_type, alert_id

  return None, None, alert_type, alert_id

def trigger_jenkins_job(script_name, alert_name, alert_type, alert_id, from_email, subject, body):
  if not alert_id:
      logging.error("❌ ALERT_ID no encontrado, no se puede lanzar el job en Jenkins")
      return False

  url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
  body_param = body if len(body) <= 8000 else body[:8000] + "\n...(truncated)..."

  params = {
      "SCRIPT_NAME": script_name,
      "ALERT_NAME": alert_name or "",
      "ALERT_TYPE": alert_type or "",
      "ALERT_ID": alert_id,
      "EMAIL_FROM": from_email or "",
      "EMAIL_SUBJECT": subject or "",
      "EMAIL_BODY": body_param
  }

  logging.info(f"Lanzando Job Jenkins con params: {params}")

  try:
      resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=30)
      if resp.status_code in (200, 201, 202):
          logging.info("✅ Jenkins job lanzado correctamente.")
          return True
      else:
          logging.error(f"Jenkins respondió: {resp.status_code} - {resp.text}")
          return False
  except Exception as e:
      logging.error(f"Fallo al llamar a Jenkins: {e}")
      return False

def check_email():
  try:
      with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as server:
          server.login(EMAIL_USER, EMAIL_PASS)
          server.select_folder("INBOX")
          messages = server.search(["UNSEEN"])
          logging.info(f"Correos no leídos: {len(messages)}")

          for msgid, data in server.fetch(messages, ['RFC822']).items():
              email_message = message_from_bytes(data[b'RFC822'])
              from_email = email_message.get('From', '').lower()
              subject_raw = email_message.get('Subject', '')
              subject = decode_mime_words(subject_raw)
              logging.info(f"Revisando correo de {from_email} | Asunto: {subject}")
              body = parse_email_body(email_message)
              alert_name, script_to_run, alert_type, alert_id = detect_alert(from_email, subject, body)

              # Marcar como leído
              server.add_flags(msgid, ['\\Seen'])

              if script_to_run and alert_id:
                  trigger_jenkins_job(script_to_run, alert_name, alert_type, alert_id, from_email, subject, body)
              else:
                  logging.error("❌ No coincide con ninguna alerta configurada o falta ALERT_ID.")
  except Exception as e:
      logging.error(f"Error en check_email: {e}")

if __name__ == "__main__":
  logging.info("Listener de correo ejecutado desde Jenkins…")
  check_email()
