# src/runner.py
import argparse
import subprocess
import sys
import os
from dispatcher.loader import load_script_path

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())

def main():
  parser = argparse.ArgumentParser(description="Dispatcher de scripts de automatización")
  parser.add_argument(
      "--script",
      required=True,
      help="Nombre del script a ejecutar (según registry)"
  )
  parser.add_argument(
      "--profile",
      default=os.path.join(WORKSPACE, "profiles", "selenium_cert"),
      help="Ruta al perfil de selenium (opcional)"
  )
  # Nuevos parámetros para datos del correo
  parser.add_argument("--alert-name", help="Nombre de la alerta detectada")
  parser.add_argument("--from-email", help="Remitente del correo")
  parser.add_argument("--subject", help="Asunto del correo")
  parser.add_argument("--body", help="Cuerpo del correo")

  args = parser.parse_args()

  # Validar que el script existe en el registry
  try:
      script_relpath = load_script_path(args.script)
  except Exception as e:
      print(f"[ERROR] {e}")
      sys.exit(1)

  script_abspath = os.path.join(WORKSPACE, script_relpath)
  if not os.path.exists(script_abspath):
      print(f"[ERROR] Script no encontrado en: {script_abspath}")
      sys.exit(1)

  print(f"[INFO] Ejecutando script: {script_abspath}")

  # Construir comando para ejecutar el script
  cmd = [sys.executable, script_abspath, args.profile]

  # Si el script necesita los datos del correo, se los pasamos como argumentos
  if args.alert_name:
      cmd.append(args.alert_name)
  if args.from_email:
      cmd.append(args.from_email)
  if args.subject:
      cmd.append(args.subject)
  if args.body:
      cmd.append(args.body)

  try:
      proc = subprocess.run(cmd, check=False)
      rc = proc.returncode
      print(f"[INFO] Proceso finalizado con código: {rc}")
  except Exception as e:
      print(f"[ERROR] Fallo al ejecutar el script: {e}")
      rc = 1

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
      sys.exit(1)  # Error técnico si no hay status.txt

  # Salida: 0 si éxito (falso_positivo), 1 si alarma_confirmada o error
  if status == "falso_positivo":
      sys.exit(0)
  else:
      sys.exit(1)

if __name__ == "__main__":
  main()
