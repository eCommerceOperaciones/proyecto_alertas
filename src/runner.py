import argparse
import subprocess
import sys
import os
import logging
from datetime import datetime
from dispatcher.loader import load_script_path

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  datefmt="%Y-%m-%d %H:%M:%S"
)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())

def main():
  parser = argparse.ArgumentParser(description="Dispatcher de scripts de automatización")
  parser.add_argument("--script", required=True, help="Nombre del script a ejecutar (según registry)")
  parser.add_argument("--profile", default=os.path.join(WORKSPACE, "profiles", "selenium_cert"),
                      help="Ruta al perfil de selenium (opcional)")
  parser.add_argument("--alert-name", help="Nombre de la alerta detectada")
  parser.add_argument("--from-email", help="Remitente del correo")
  parser.add_argument("--subject", help="Asunto del correo")
  parser.add_argument("--body", help="Cuerpo del correo (opcional, puede venir de variable de entorno)")
  parser.add_argument("--retry", type=int, default=0, help="Número de reintentos ejecutados")
  parser.add_argument("--max-retries", type=int, default=1, help="Número máximo de reintentos permitidos")

  args = parser.parse_args()

  alert_name = args.alert_name or os.getenv("ALERT_NAME", "")
  from_email = args.from_email or os.getenv("EMAIL_FROM", "")
  subject = args.subject or os.getenv("EMAIL_SUBJECT", "")
  body = args.body or os.getenv("EMAIL_BODY", "")
  alert_id = os.getenv("ALERT_ID", "no_id")

  logging.info(f"Script: {args.script}")
  logging.info(f"Perfil Selenium: {args.profile}")
  logging.info(f"Alerta: {alert_name}")
  logging.info(f"Retry actual: {args.retry} / Máx: {args.max_retries}")
  logging.info(f"ALERT_ID: {alert_id}")

  try:
      script_relpath = load_script_path(args.script)
  except Exception as e:
      logging.error(e)
      sys.exit(2)

  script_abspath = os.path.join(WORKSPACE, script_relpath)
  if not os.path.exists(script_abspath):
      logging.error(f"Script no encontrado en: {script_abspath}")
      sys.exit(2)

  run_dir = os.path.join(WORKSPACE, "runs", alert_id)
  logs_dir = os.path.join(run_dir, "logs")
  screenshots_dir = os.path.join(run_dir, "screenshots")
  os.makedirs(logs_dir, exist_ok=True)
  os.makedirs(screenshots_dir, exist_ok=True)

  log_file = os.path.join(logs_dir, "execution.log")
  status_file_workspace = os.path.join(WORKSPACE, "status.txt")

  cmd = [sys.executable, script_abspath, args.profile, alert_name, from_email, subject, body]

  try:
      with open(log_file, "w") as lf:
          proc = subprocess.run(cmd, stdout=lf, stderr=lf, check=False)
      rc = proc.returncode
      logging.info(f"Proceso finalizado con código: {rc}")
  except Exception as e:
      logging.error(f"Fallo al ejecutar el script: {e}")
      sys.exit(2)

  status = None
  if os.path.exists(status_file_workspace):
      try:
          with open(status_file_workspace, "r") as f:
              status = f.read().strip()
      except Exception as e:
          logging.warning(f"No se pudo leer status.txt: {e}")
  else:
      logging.error("status.txt no encontrado en workspace")
      sys.exit(2)

  if status:
      logging.info(f"status.txt => {status}")
  else:
      logging.error("status.txt vacío")
      sys.exit(2)

  if status == "falso_positivo":
      logging.info("Resultado: falso_positivo → Jenkins decidirá si reintenta")
      sys.exit(0)
  elif status == "alarma_confirmada":
      logging.info("Resultado: alarma_confirmada → Jenkins continuará flujo alerta real")
      sys.exit(0)
  else:
      logging.error(f"Estado desconocido: {status}")
      sys.exit(2)

if __name__ == "__main__":
  main()
