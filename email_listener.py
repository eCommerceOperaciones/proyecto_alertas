import os
import time
import requests
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from bs4 import BeautifulSoup

# Cargar variables de entorno
load_dotenv()

# CONFIGURACIÓN CORREO
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# CONFIGURACIÓN JENKINS
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_alertas")

# FILTROS
FROM_FILTER = "rpinheiro@viewnext.com"
BODY_FILTER = "ACCES FRONTAL EMD"
SCRIPT_NAME = "main.py"

def trigger_jenkins_job(script_name):
    url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
    params = {"SCRIPT_NAME": script_name}
    print(f"[DEBUG] Llamando a Jenkins: {url} con params {params}")
    resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN))
    print(f"[DEBUG] Respuesta Jenkins: {resp.status_code} - {resp.text}")
    if resp.status_code == 201:
        print(f"[INFO] Job {JOB_NAME} lanzado correctamente con SCRIPT_NAME={script_name}")
    else:
        print(f"[ERROR] No se pudo lanzar el job: {resp.status_code} - {resp.text}")

def check_email():
    with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.select_folder("INBOX")
        messages = server.search(['UNSEEN'])
        print(f"[DEBUG] Correos no leídos encontrados: {len(messages)}")
        for msgid, data in server.fetch(messages, ['RFC822']).items():
            email_message = message_from_bytes(data[b'RFC822'])
            from_email = email_message.get('From', '').lower()
            subject = email_message.get('Subject', '')
            print(f"[DEBUG] Revisando correo: {subject} de {from_email}")

            # Extraer cuerpo
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() in ["text/plain", "text/html"]:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        if part.get_content_type() == "text/html":
                            body = BeautifulSoup(body, "html.parser").get_text()
                        break
            else:
                body = email_message.get_payload(decode=True).decode(errors="ignore")

            print(f"[DEBUG] Cuerpo del correo:\n{body}")

            # Filtrar
            if FROM_FILTER.lower() in from_email and BODY_FILTER.lower() in body.lower():
                print(f"[INFO] Alerta detectada de {from_email} con asunto: {subject}")
                trigger_jenkins_job(SCRIPT_NAME)
                server.add_flags(msgid, [b'\\Seen'])
            else:
                print(f"[DEBUG] Correo ignorado: no coincide con filtros")

if __name__ == "__main__":
    print("[INFO] Iniciando escucha de correo...")
    while True:
        try:
            check_email()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(60)
