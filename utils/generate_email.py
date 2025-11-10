import os
import re

def extract_fecha_inicio(body):
    match = re.search(r"Inici:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})", body)
    return match.group(1) if match else "Desconegut"

def load_template(script_name):
    template_path = os.path.join("email_templates", f"{script_name}.html")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Plantilla no encontrada para {script_name}")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_email(script_name, body):
    fecha_inicio = extract_fecha_inicio(body)
    template = load_template(script_name)
    return template.replace("{{fecha_inicio}}", fecha_inicio)

if __name__ == "__main__":
    script_name = os.getenv("SCRIPT_NAME", "")
    email_body = os.getenv("EMAIL_BODY", "")
    html_email = generate_email(script_name, email_body)
    print(html_email)
