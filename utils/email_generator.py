# utils/email_generator.py
import os
import re
import uuid

def extract_fecha_inicio(body):
    match = re.search(r"(Inici|Recepció):\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})", body)
    return match.group(2) if match else "Desconegut"

def extract_fecha_resolucion(body):
    match = re.search(r"Recuperació:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", body)
    return match.group(1) if match else ""

def load_template(script_name):
    template_path = os.path.join("email_templates", f"{script_name}.html")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Plantilla no encontrada para {script_name}")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_email_and_excel_fields(script_name, body, alert_type, alert_id=None):
    """Genera el HTML del correo y los campos para el Excel."""
    fecha_inicio = extract_fecha_inicio(body)
    fecha_resolucion = extract_fecha_resolucion(body) if alert_type == "RESUELTA" else ""

    template = load_template(script_name)
    html_email = template.replace("{{fecha_inicio}}", fecha_inicio)

    if not alert_id:
        alert_id = str(uuid.uuid4())

    excel_fields = {
        "ID": alert_id,
        "Inici": fecha_inicio,
        "Fi": fecha_resolucion,
        "Afecta a": "Ciutadania / Funcionari",  # Ajustar si es dinámico
        "Incidència": script_name,
        "Parcial/Total": "PARCIAL",
        "Origen": "CPD4",
        "Descripción": "Generado desde plantilla"
    }

    return html_email, excel_fields
