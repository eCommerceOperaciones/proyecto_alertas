import os
import re
import json
import logging
from dotenv import load_dotenv
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv()

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

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
    },
    "Area Privada": {
        "from": "rpinheiro@viewnext.com",
        "subject_contains": "AREA PRIVADA",
        "body_contains": "CARPETA_CIUTADANA-CONF",
        "script": "area_privada"
    }
}

def decode_mime_words(s):
    try:
        return str(make_header(decode_header(s)))
    except:
        return s or ""

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^\w\s]", " ", text)
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
    match = re.search(r"Recepci[oó]:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
    if match:
        fecha_hora = match.group(1)
        try:
            dt = datetime.strptime(fecha_hora, "%d/%m/%Y %H:%M:%S")
            return dt.strftime("%Y%m%d_%H%M%S")
        except ValueError:
            logging.error(f"Formato de fecha/hora inválido en Recepció: {fecha_hora}")
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
        return None, None, alert_type, None

    for alert_name, data in ALERTS.items():
        match = True
        if "from" in data and normalize_text(data["from"]) not in from_norm:
            match = False
        if "subject_contains" in data and normalize_text(data["subject_contains"]) not in subject_norm:
            match = False
        if "body_contains" in data and normalize_text(data["body_contains"]) not in body_norm:
            match = False
        if match:
            return alert_name, data["script"], alert_type, alert_id
    return None, None, alert_type, alert_id

def check_email():
    alerts_found = []
    try:
        with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.select_folder("INBOX")
            messages = server.search(["UNSEEN"])
            logging.info(f"Correos no leídos: {len(messages)}")

            for msgid, data in server.fetch(messages, ['RFC822']).items():
                email_message = message_from_bytes(data[b'RFC822'])
                from_email = (email_message.get('From') or '').lower()
                subject_raw = email_message.get('Subject') or ''
                subject = decode_mime_words(subject_raw)
                body = parse_email_body(email_message)

                alert_name, script_to_run, alert_type, alert_id = detect_alert(from_email, subject, body)

                if script_to_run and alert_id:
                    alerts_found.append({
                        "alert_name": alert_name,
                        "script": script_to_run,
                        "alert_type": alert_type,
                        "alert_id": alert_id,
                        "email_from": from_email,
                        "email_subject": subject,
                        "email_body": body
                    })
                    # Solo marcar como leído si es alerta válida
                    server.add_flags(msgid, ['\\Seen'])

    except Exception as e:
        logging.error(f"Error en check_email: {e}")

    print(json.dumps(alerts_found))

if __name__ == "__main__":
    check_email()
