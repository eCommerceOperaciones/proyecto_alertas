import os
import json

# Esta función es solo para desarrollo y pruebas
def print_email_data(log, EMAIL_DATA_PATH):
  """
  Imprime el contenido del archivo email_data.json para validar que está correcto.
  Parámetros:
      log (func): función de logging que recibe (nivel, mensaje)
      EMAIL_DATA_PATH (str): ruta al archivo email_data.json
  """
  if os.path.exists(EMAIL_DATA_PATH):
      try:
          with open(EMAIL_DATA_PATH, "r", encoding="utf-8") as f:
              email_data = json.load(f)
          log("info", "=== Datos del correo que disparó la alerta ===")
          log("info", f"Alerta: {email_data.get('alert_name')}")
          log("info", f"Remitente: {email_data.get('from_email')}")
          log("info", f"Asunto: {email_data.get('subject')}")
          log("info", f"Cuerpo: {email_data.get('body')}")
      except Exception as e:
          log("error", f"No se pudo leer email_data.json: {e}")
  else:
      log("warn", "No se encontró email_data.json")
