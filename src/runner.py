# src/runner.py
import argparse
import subprocess
import sys
import os
from dispatcher.loader import load_script_path

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())

def main():
  parser = argparse.ArgumentParser(description="Dispatcher de scripts de automatización")
  parser.add_argument("--script", required=True, help="Nombre del script a ejecutar (según registry)")
  parser.add_argument("--profile", default=os.path.join(WORKSPACE, "profiles", "selenium_cert"),
                      help="Ruta al perfil de selenium (opcional)")
  parser.add_argument("--alert-name", help="Nombre de la alerta detectada")
  parser.add_argument("--from-email", help="Remitente del correo")
  parser.add_argument("--subject", help="Asunto del correo")
  parser.add_argument("--body", help="Cuerpo del correo")
  parser.add_argument("--retry", type=int, default=0, help="Número de reintentos ejecutados")
  parser.add_argument("--max-retries", type=int, default=1, help="Número máximo de reintentos permitidos")

  args = parser.parse_args()

  # Si no se pasan por CLI, leer de variables de entorno
  alert_name = args.alert_name or os.getenv("ALERT_NAME", "")
  from_email = args.from_email or os.getenv("EMAIL_FROM", "")
  subject = args.subject or os.getenv("EMAIL_SUBJECT", "")
  body = args.body or os.getenv("EMAIL_BODY", "")

  print(f"[INFO] Script: {args.script}")
  print(f"[INFO] Perfil Selenium: {args.profile}")
  print(f"[INFO] Alerta: {alert_name}")
  print(f"[INFO] Retry actual: {args.retry} / Máx: {args.max_retries}")

  # Validar que el script existe en el registry
  try:
      script_relpath = load_script_path(args.script)
  except Exception as e:
      print(f"[ERROR] {e}")
      sys.exit(2)  # Error técnico

  script_abspath = os.path.join(WORKSPACE, script_relpath)
  if not os.path.exists(script_abspath):
      print(f"[ERROR] Script no encontrado en: {script_abspath}")
      sys.exit(2)

  print(f"[INFO] Ejecutando script: {script_abspath}")

  # Construir comando para ejecutar el script
  cmd = [sys.executable, script_abspath, args.profile, alert_name, from_email, subject, body]

  try:
      proc = subprocess.run(cmd, check=False)
      rc = proc.returncode
      print(f"[INFO] Proceso finalizado con código: {rc}")
  except Exception as e:
      print(f"[ERROR] Fallo al ejecutar el script: {e}")
      sys.exit(2)

  # Leer status.txt que crea el script
  status_file = os.path.join(WORKSPACE, "status.txt")
  status = None
  if os.path.exists(status_file):
      try:
          with open(status_file, "r") as f:
              status = f.read().strip()
      except Exception as e:
          print(f"[WARN] No se pudo leer status.txt: {e}")
  else:
      print("[WARN] status.txt no encontrado")

  if status:
      print(f"[INFO] status.txt => {status}")
  else:
      print("[ERROR] status.txt no encontrado o vacío")
      sys.exit(2)  # Error técnico

  # Salida según estado
  if status == "falso_positivo":
      sys.exit(0)  # Éxito, pero requiere posible reintento
  elif status == "alarma_confirmada":
      sys.exit(1)  # Alarma confirmada
  else:
      print(f"[ERROR] Estado desconocido: {status}")
      sys.exit(2)  # Error técnico

if __name__ == "__main__":
  main()
