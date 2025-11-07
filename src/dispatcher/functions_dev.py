import os, json

def print_email_data(log, EMAIL_DATA_PATH):
  if EMAIL_DATA_PATH and os.path.exists(EMAIL_DATA_PATH):
      with open(EMAIL_DATA_PATH, "r", encoding="utf-8") as f:
          email_data = json.load(f)
      log("info", "=== Datos del correo que disparó la alerta ===")
      log("info", f"Alerta: {email_data.get('alert_name')}")
      log("info", f"Remitente: {email_data.get('from_email')}")
      log("info", f"Asunto: {email_data.get('subject')}")
      log("info", f"Cuerpo: {email_data.get('body')}")
  else:
      log("warn", "No se encontró email_data.json para esta ejecución")
