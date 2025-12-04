import os
import re
import uuid

# =========================
# Funciones auxiliares
# =========================
def load_template(template_name):
    """
    Carga una plantilla HTML desde la carpeta email_templates.
    """
    path = os.path.join("email_templates", f"{template_name}.html")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plantilla no encontrada: {template_name}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def clean_tokens(html):
    """
    Elimina cualquier token ${...} que pueda romper emailext.
    """
    return re.sub(r"\$\{.*?\}", "", html)

def extract_fecha_inicio(body):
    match = re.search(r"(Inici|Recepció):\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})", body)
    return match.group(2) if match else "Desconegut"

def extract_fecha_resolucion(body):
    match = re.search(r"Recuperació:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
    return match.group(1) if match else ""

# =========================
# Generadores de correo
# =========================
def generate_error_email(script_name, alert_name, alert_type, alert_id, error_message, retry_count, max_retries):
    template = load_template("error")
    html = (template
            .replace("{{script_name}}", script_name)
            .replace("{{alert_name}}", alert_name)
            .replace("{{alert_type}}", alert_type)
            .replace("{{alert_id}}", alert_id)
            .replace("{{error_message}}", error_message)
            .replace("{{retry_count}}", str(retry_count))
            .replace("{{max_retries}}", str(max_retries)))
    return clean_tokens(html)

def generate_false_positive_email(script_name, alert_name, alert_type, alert_id, job_name):
    template = load_template("false_positive")
    html = (template
            .replace("{{script_name}}", script_name)
            .replace("{{alert_name}}", alert_name)
            .replace("{{alert_type}}", alert_type)
            .replace("{{alert_id}}", alert_id)
            .replace("{{job_name}}", job_name))
    return clean_tokens(html)

def generate_alert_email(script_name, body, alert_type, alert_id=None):
    fecha_inicio = extract_fecha_inicio(body)
    fecha_resolucion = extract_fecha_resolucion(body) if alert_type == "RESUELTA" else ""

    template = load_template(script_name)
    html_email = (template
                  .replace("{{fecha_inicio}}", fecha_inicio)
                  .replace("{{fecha_resolucion}}", fecha_resolucion))

    if not alert_id:
        alert_id = str(uuid.uuid4())

    excel_fields = {
        "ID": alert_id,
        "Inici": fecha_inicio,
        "Fi": fecha_resolucion,
        "Afecta a": "Ciutadania / Funcionari",
        "Incidència": script_name,
        "Parcial/Total": "PARCIAL",
        "Origen": "CPD4",
        "Descripción": "Generado desde plantilla"
    }

    return clean_tokens(html_email), excel_fields
