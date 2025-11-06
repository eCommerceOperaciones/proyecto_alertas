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

load_dotenv()

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
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
# Puedes añadir nuevas alertas aquí fácilmente.
ALERTS = {
    "ACCES FRONTAL EMD": {
        "from": "rpinheiro@viewnext.com",
        "script": "acces_frontal_emd"
    },

    # Ejemplo futura alerta:
    # "ACCES SANITARI": {
    #     "from": "otrocorreo@empresa.com",
    #     "script": "acces_sanitari.py"
    # },
}


# ============================
# FUNCIONES
# ============================

def trigger_jenkins_job(script_name):
    """
    Lanza un job Jenkins y pasa el script correcto al dispatcher.
    """

    url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
    params = {"SCRIPT_NAME": script_name}

    print(f"[INFO] Lanzando job Jenkins con SCRIPT_NAME={script_name}")

    try:
        resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN))

        # Si el job NO es parametrizado → fallback
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
    Extrae texto del email, incluso si es HTML.
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


def detect_alert(from_email, body):
    """
    Determina qué alerta corresponde al email.
    """

    for alert_name, data in ALERTS.items():
        if data["from"].lower() in from_email.lower() and alert_name.lower() in body.lower():
            print(f"[INFO] ✅ Alerta detectada: {alert_name}")
            return data["script"]

    return None


def check_email():
    """
    Revisa el buzón IMAP, detecta alertas y llama a Jenkins.
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
            script_to_run = detect_alert(from_email, body)

            if script_to_run:
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

        time.sleep(60)  # Espera 1 minuto por ciclo
