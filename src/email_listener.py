# =========================
# email_listener.py (sin JSON)
# =========================
import os
import time
import re
import requests
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from datetime import datetime

# ============================
# Cargar variables de entorno
# ============================
load_dotenv()

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Jenkins
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_Alertas_Pruebas")

# ============================
# Alertas configuradas
# ============================
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

# ============================
# Funciones
# ============================
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

def detect_alert(from_email, subject, body):
  from_norm = normalize_text(from_email)
  subject_norm = normalize_text(subject)
  body_norm = normalize_text(body)

  for alert_name, data in ALERTS.items():
      match = True
      if "from" in data and normalize_text(data["from"]) not in from_norm:
          match = False
      if "subject_contains" in data and normalize_text(data["subject_contains"]) not in subject_norm:
          match = False
      if "body_contains" in data and normalize_text(data["body_contains"]) not in body_norm:
          match = False
      if match:
          print(f"[INFO] ✅ Alerta detectada: {alert_name}")
          return alert_name, data["script"]
  return None, None

def trigger_jenkins_job(script_name, alert_name, from_email, subject, body):
  """
  Lanza job en Jenkins pasando todos los datos como parámetros.
  """
  url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
  body_param = body if len(body) <= 8000 else body[:8000] + "\n...(truncated)..."

  params = {
      "SCRIPT_NAME": script_name,
      "ALERT_NAME": alert_name or "",
      "EMAIL_FROM": from_email or "",
      "EMAIL_SUBJECT": subject or "",
      "EMAIL_BODY": body_param
  }

  print(f"[INFO] Lanzando Job Jenkins con params: {params}")

  try:
      resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=30)
      if resp.status_code in (200, 201, 202):
          print("[INFO] ✅ Jenkins job lanzado correctamente.")
          return True
      else:
          print(f"[ERROR] Jenkins respondió: {resp.status_code} - {resp.text}")
          return False
  except Exception as e:
      print(f"[ERROR] Fallo al llamar a Jenkins: {e}")
      return False

def check_email():
  with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as server:
      server.login(EMAIL_USER, EMAIL_PASS)
      server.select_folder("INBOX")
      messages = server.search(["UNSEEN"])
      print(f"[INFO] Correos no leídos: {len(messages)}")

      for msgid, data in server.fetch(messages, ['RFC822']).items():
          email_message = message_from_bytes(data[b'RFC822'])
          from_email = email_message.get('From', '').lower()
          subject_raw = email_message.get('Subject', '')
          subject = decode_mime_words(subject_raw)
          print(f"[INFO] Revisando correo de {from_email} | Asunto: {subject}")
          body = parse_email_body(email_message)
          alert_name, script_to_run = detect_alert(from_email, subject, body)

          if script_to_run:
              trigger_jenkins_job(script_to_run, alert_name, from_email, subject, body)
          else:
              print("[INFO] No coincide con ninguna alerta configurada.")

# ============================
# Loop principal
# ============================
if __name__ == "__main__":
  print("[INFO] Listener de correo iniciado…")
  while True:
      try:
          check_email()
      except Exception as e:
          print(f"[ERROR] Error general del listener: {e}")
      time.sleep(60)
