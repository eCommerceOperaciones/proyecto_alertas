# =========================
# email_listener.py (final)
# =========================
import os
import json
import time
import re
import requests
import sys
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

# Workspace handling: prefer WORKSPACE env var (exportada por Jenkins), si no, usar default
DEFAULT_JENKINS_WORKSPACE = "/var/lib/jenkins/workspace/GSIT_Alertas_Pruebas"
WORKSPACE = os.getenv("WORKSPACE") or DEFAULT_JENKINS_WORKSPACE

# Si no existe la ruta, intentamos crearla (puede fallar por permisos)
try:
    os.makedirs(WORKSPACE, exist_ok=True)
except Exception as e:
    print(f"[WARN] No se pudo crear/usar WORKSPACE '{WORKSPACE}': {e}")
    # fallback a cwd/runs
    WORKSPACE = os.path.abspath(os.getcwd())
    print(f"[WARN] Usando fallback WORKSPACE local: {WORKSPACE}")

print(f"[INFO] Listener usando WORKSPACE: {WORKSPACE}")

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

def save_email_data(alert_name, from_email, subject, body):
    """
    Guarda los datos del correo en runs/<run_id>/email_data.json dentro del WORKSPACE,
    y actualiza email_data_path.txt y current_run.txt en la raíz del WORKSPACE.
    Devuelve la ruta absoluta del email_data.json o None si fallo.
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(WORKSPACE, "runs", run_id)

    try:
        os.makedirs(run_dir, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] No se pudo crear run_dir '{run_dir}': {e}")
        return None

    email_data_path = os.path.join(run_dir, "email_data.json")
    try:
        with open(email_data_path, "w", encoding="utf-8") as f:
            json.dump({
                "alert_name": alert_name,
                "from_email": from_email,
                "subject": subject,
                "body": body
            }, f, ensure_ascii=False, indent=4)

        # escribir referencias en la raíz del workspace
        with open(os.path.join(WORKSPACE, "email_data_path.txt"), "w", encoding="utf-8") as f:
            f.write(email_data_path)

        with open(os.path.join(WORKSPACE, "current_run.txt"), "w", encoding="utf-8") as f:
            f.write(run_id)

        print(f"[INFO] Datos del correo guardados en: {email_data_path}")
        return email_data_path

    except Exception as e:
        print(f"[ERROR] Error guardando email_data.json: {e}")
        return None

def trigger_jenkins_job(script_name, alert_name, from_email, subject, body, prefer_file=False):
    """
    Lanza job en Jenkins.
    - Si prefer_file==True asumimos que save_email_data ya creó email_data.json y Jenkins leerá desde workspace.
    - De todas formas, también pasamos SCRIPT_NAME como parámetro (útil).
    """
    url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
    # Cortamos body grande para pasarlo como parámetro si es necesario (parametros tienen límites)
    body_param = body if len(body) <= 8000 else body[:8000] + "\n...(truncated)..."

    params = {
        "SCRIPT_NAME": script_name,
        "ALERT_NAME": alert_name or "",
        "EMAIL_FROM": from_email or "",
        "EMAIL_SUBJECT": subject or "",
        "EMAIL_BODY": body_param
    }

    print(f"[INFO] Lanzando Job Jenkins con params: SCRIPT_NAME={script_name}, ALERT_NAME={alert_name}")

    try:
        resp = requests.post(url, params=params, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=30)
        # algunos Jenkins devuelven 201/200/202 según configuración
        if resp.status_code in (200, 201, 202):
            print("[INFO] ✅ Jenkins job lanzado correctamente.")
            return True
        else:
            # Si job no está parametrizado, intentar build simple
            if resp.status_code == 400 and "is not parameterized" in (resp.text or ""):
                print("[WARN] Job no parametrizado. Intentando build simple.")
                url_simple = f"{JENKINS_URL}/job/{JOB_NAME}/build"
                resp2 = requests.post(url_simple, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=30)
                if resp2.status_code in (200, 201, 202):
                    print("[INFO] ✅ Jenkins job lanzado con build simple.")
                    return True
            print(f"[ERROR] Jenkins respondió: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Fallo al llamar a Jenkins: {e}")
        return False

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
                # Intentamos primero escribir el JSON en WORKSPACE (si es accesible)
                saved_path = save_email_data(alert_name, from_email, subject, body)
                if saved_path:
                    # Si guardamos correctamente, preferimos que Jenkins lea el archivo desde su workspace.
                    success = trigger_jenkins_job(script_to_run, alert_name, from_email, subject, body, prefer_file=True)
                    if not success:
                        print("[WARN] Jenkins trigger falló aun habiendo creado el JSON. Intentando trigger sin file.")
                        trigger_jenkins_job(script_to_run, alert_name, from_email, subject, body, prefer_file=False)
                else:
                    # No hemos podido guardar el JSON (permissions / ruta no accesible).
                    # Lanzamos job con parámetros para que Jenkins tenga la info mínima posible.
                    print("[WARN] No se pudo guardar email_data.json en WORKSPACE. Lanzando job con parámetros como fallback.")
                    trigger_jenkins_job(script_to_run, alert_name, from_email, subject, body, prefer_file=False)
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
