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
  parser.add_argument("--body", help="Cuerpo del correo")
  parser.add_argument("--retry", type=int, default=0, help="Número de reintentos ejecutados")
  parser.add_argument("--max-retries", type=int, default=1, help="Número máximo de reintentos permitidos")

  args = parser.parse_args()

  alert_name = args.alert_name or os.getenv("ALERT_NAME", "")
  from_email = args.from_email or os.getenv("EMAIL_FROM", "")
  subject = args.subject or os.getenv("EMAIL_SUBJECT", "")
  body = args.body or os.getenv("EMAIL_BODY", "")

  logging.info(f"Script: {args.script}")
  logging.info(f"Perfil Selenium: {args.profile}")
  logging.info(f"Alerta: {alert_name}")
  logging.info(f"Retry actual: {args.retry} / Máx: {args.max_retries}")

  try:
      script_relpath = load_script_path(args.script)
  except Exception as e:
      logging.error(e)
      sys.exit(2)  # Error técnico

  script_abspath = os.path.join(WORKSPACE, script_relpath)
  if not os.path.exists(script_abspath):
      logging.error(f"Script no encontrado en: {script_abspath}")
      sys.exit(2)  # Error técnico

  os.makedirs(os.path.join(WORKSPACE, "runs", "logs"), exist_ok=True)
  log_file = os.path.join(WORKSPACE, "runs", "logs", f"{args.script}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

  cmd = [sys.executable, script_abspath, args.profile, alert_name, from_email, subject, body]

  try:
      with open(log_file, "w") as lf:
          proc = subprocess.run(cmd, stdout=lf, stderr=lf, check=False)
      rc = proc.returncode
      logging.info(f"Proceso finalizado con código: {rc}")
  except Exception as e:
      logging.error(f"Fallo al ejecutar el script: {e}")
      sys.exit(2)  # Error técnico

  status_file = os.path.join(WORKSPACE, "status.txt")
  status = None
  if os.path.exists(status_file):
      try:
          with open(status_file, "r") as f:
              status = f.read().strip()
      except Exception as e:
          logging.warning(f"No se pudo leer status.txt: {e}")
  else:
      logging.warning("status.txt no encontrado")

  if status:
      logging.info(f"status.txt => {status}")
  else:
      logging.error("status.txt no encontrado o vacío")
      sys.exit(2)  # Error técnico

  # ✅ Ajuste: alarma_confirmada ahora devuelve exit code 0 para que Jenkins continúe
  if status == "falso_positivo":
      sys.exit(0)  # Éxito, pero requiere posible reintento
  elif status == "alarma_confirmada":
      sys.exit(0)  # Éxito, continuar flujo alerta real
  else:
      logging.error(f"Estado desconocido: {status}")
      sys.exit(2)  # Error técnico

if __name__ == "__main__":
  main()
