# =========================
# email_listener.py
# =========================
"""
Script que escucha correos electrónicos entrantes en una cuenta IMAP y,
según el contenido, remitente, asunto y cuerpo, lanza un job en Jenkins
para ejecutar scripts específicos asociados a alertas configuradas.
"""

import os
import time
import requests
import re
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
import json

# ============================
# CARGAR VARIABLES DE ENTORNO
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
# ALERTAS CONFIGURADAS
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
# FUNCIONES
# ============================

def decode_mime_words(s):
  """Decodifica un asunto MIME a texto normal."""
  try:
      return str(make_header(decode_header(s)))
  except:
      return s

def normalize_text(text):
  """Convierte texto a minúsculas y quita espacios y saltos de línea."""
  return re.sub(r'\s+', ' ', text.strip().lower())

def trigger_jenkins_job(script_name):
  """Lanza un job en Jenkins con el parámetro SCRIPT_NAME."""
  url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
  params = {"SCRIPT_NAME": script_name}

  print(f"[INFO] Lanzando job Jenkins con SCRIPT_NAME={script_name}")

  try:
      resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN))

      if resp.status_code == 400 and "is not parameterized" in resp.text:
          print("[WARN] Job no parametrizado. Usando build simple.")
          url = f"{JENKINS_URL}/job/{JOB_NAME}/build"
          resp = requests.post(url, auth=(JENKINS_USER, JENKINS_TOKEN))

      if resp.status_code in [200, 201]:
          print(f"[INFO] ✅ Job ejecutado correctamente")
          return True
      else:
          print(f"[ERROR] Jenkins error: {resp.status_code} - {resp.text}")
          return False

  except Exception as e:
      print(f"[ERROR] Jenkins request failed: {e}")
      return False

def parse_email_body(email_message):
  """Extrae el cuerpo del correo electrónico y lo convierte a texto plano si es HTML."""
  body = ""

  if email_message.is_multipart():
      for part in email_message.walk():
          content_type = part.get_content_type()

          if content_type in ["text/plain", "text/html"]:
              body = part.get_payload(decode=True).decode(errors="ignore")

              if content_type == "text/html":
                  body = BeautifulSoup(body, "html.parser").get_text()

              break
  else:
      body = email_message.get_payload(decode=True).decode(errors="ignore")

  return body

def detect_alert(from_email, subject, body):
    from_email_norm = normalize_text(from_email)
    subject_norm = normalize_text(subject)
    body_norm = normalize_text(body)

    for alert_name, data in ALERTS.items():
        match = True

        if "from" in data and normalize_text(data["from"]) not in from_email_norm:
            match = False
        if "subject_contains" in data and normalize_text(data["subject_contains"]) not in subject_norm:
            match = False
        if "body_contains" in data and normalize_text(data["body_contains"]) not in body_norm:
            match = False

        if match:
            print(f"[INFO] ✅ Alerta detectada: {alert_name}")
            return alert_name, data["script"]  # devolvemos ambos valores

    return None, None

def save_email_data(alert_name, from_email, subject, body):
  email_data = {
      "alert_name": alert_name,
      "from_email": from_email,
      "subject": subject,
      "body": body
  }
  with open("email_data.json", "w", encoding="utf-8") as f:
      json.dump(email_data, f, ensure_ascii=False, indent=4)

def check_email():
  """Conecta al servidor IMAP, busca correos no leídos y detecta alertas."""
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
              save_email_data(alert_name, from_email, subject, body)
              trigger_jenkins_job(script_to_run)
              server.add_flags(msgid, [b'\\Seen'])
          else:
              print("[INFO] No coincide con ninguna alerta configurada.")

# ============================
# MAIN LOOP
# ============================
if __name__ == "__main__":
  print("[INFO] Listener de correo iniciado...")

  while True:
      try:
          check_email()
      except Exception as e:
          print(f"[ERROR] Listener error: {e}")

      time.sleep(60)
