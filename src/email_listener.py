# =========================
# email_listener.py
# =========================
"""
Script que escucha correos electrónicos entrantes en una cuenta IMAP y,
según el contenido y remitente, lanza un job en Jenkins para ejecutar
scripts específicos asociados a alertas configuradas.
"""

import os
import time
import requests
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from bs4 import BeautifulSoup

# ============================
# CARGAR VARIABLES DE ENTORNO
# ============================
"""
Se cargan las credenciales y configuraciones desde un archivo .env.
Este archivo debe contener:
- EMAIL_USER: usuario de la cuenta de correo
- EMAIL_PASS: contraseña de la cuenta de correo
- JENKINS_URL: URL base del servidor Jenkins
- JENKINS_USER: usuario de Jenkins
- JENKINS_TOKEN: token de API de Jenkins
- JOB_NAME: nombre del job en Jenkins (opcional, por defecto 'GSIT_alertas')
"""
load_dotenv()

IMAP_SERVER = "imap.gmail.com"  # Servidor IMAP de Gmail
IMAP_PORT = 993  # Puerto seguro IMAP
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Jenkins
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_alertas")

# ============================
# ALERTAS CONFIGURADAS
# ============================
"""
Diccionario que define las alertas que se pueden detectar.
Cada alerta contiene:
- 'from': texto que debe aparecer en el remitente del correo
- 'script': nombre del script que se pasará como parámetro a Jenkins
"""
ALERTS = {
  "Alerta Acces Frontal": {
      "from": "rpinheiro@viewnext.com",  # opcional
      "subject_contains": "ELS MEUS DOCUMENTSD",  # opcional
      "body_contains": "ACCES_FRONTAL_EMD",  # opcional
      "script": "acces_frontal_emd.py"
  },
  "Alerta Frameworks": {
      "from": "rpinheiro@viewnext.com",
      "subject_contains": "[GSIT] - Alerta Activa - ⚠ Alertes - FRAMEWORKS EFORMULARIS",
      "body_contains": "01_CARREGA_URL_WEFOSJX26-HTTP-WSDL",
      "script": "01_carrega_url_wsdl.py"
  }
}


# ============================
# FUNCIONES
# ============================

def trigger_jenkins_job(script_name):
  """
  Lanza un job en Jenkins con el parámetro SCRIPT_NAME.
  
  Parámetros:
      script_name (str): Nombre del script que se enviará como parámetro.
  
  Flujo:
      1. Intenta lanzar el job con parámetros.
      2. Si el job no acepta parámetros, lanza un build simple.
      3. Devuelve True si se ejecuta correctamente, False en caso contrario.
  """
  url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
  params = {"SCRIPT_NAME": script_name}

  print(f"[INFO] Lanzando job Jenkins con SCRIPT_NAME={script_name}")

  try:
      resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN))

      # Fallback si el job no es parametrizado
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
  """
  Extrae el cuerpo del correo electrónico.
  
  Si el contenido es HTML, se convierte a texto plano usando BeautifulSoup.
  
  Parámetros:
      email_message (EmailMessage): Objeto de correo obtenido de IMAP.
  
  Retorna:
      str: Texto del cuerpo del correo.
  """
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
  """
  Determina si el correo coincide con alguna alerta configurada.
  Compara remitente, asunto y cuerpo según lo definido en ALERTS.
  """
  for alert_name, data in ALERTS.items():
      match = True  # asumimos que coincide hasta que falle un criterio

      if "from" in data and data["from"].lower() not in from_email.lower():
          match = False
      if "subject_contains" in data and data["subject_contains"].lower() not in subject.lower():
          match = False
      if "body_contains" in data and data["body_contains"].lower() not in body.lower():
          match = False

      if match:
          print(f"[INFO] ✅ Alerta detectada: {alert_name}")
          return data["script"]

  return None


def check_email():
  """
  Conecta al servidor IMAP, busca correos no leídos,
  detecta alertas y lanza el job correspondiente en Jenkins.
  
  Flujo:
      1. Conexión al servidor IMAP.
      2. Búsqueda de mensajes no leídos.
      3. Procesamiento de cada mensaje.
      4. Detección de alertas y ejecución de Jenkins.
      5. Marcado de mensajes como leídos si se procesan.
  """
  with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as server:
      server.login(EMAIL_USER, EMAIL_PASS)
      server.select_folder("INBOX")

      messages = server.search(["UNSEEN"])
      print(f"[INFO] Correos no leídos: {len(messages)}")

      for msgid, data in server.fetch(messages, ['RFC822']).items():
          email_message = message_from_bytes(data[b'RFC822'])

          from_email = email_message.get('From', '').lower()
          subject = email_message.get('Subject', '')

          print(f"[INFO] Revisando correo de {from_email} | Asunto: {subject}")

          body = parse_email_body(email_message)
          script_to_run = detect_alert(from_email, subject, body)

          if script_to_run:
              trigger_jenkins_job(script_to_run)
              server.add_flags(msgid, [b'\\Seen'])  # Marca como leído
          else:
              print("[INFO] No coincide con ninguna alerta configurada.")

# ============================
# MAIN LOOP
# ============================
"""
Bucle principal que revisa el correo cada minuto.
En caso de error, lo captura y continúa la ejecución.
"""
if __name__ == "__main__":
  print("[INFO] Listener de correo iniciado...")

  while True:
      try:
          check_email()
      except Exception as e:
          print(f"[ERROR] Listener error: {e}")

      time.sleep(60)  # Espera 1 minuto antes de la siguiente revisión
