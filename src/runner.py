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
  parser.add_argument(
      "--email-data",
      help="Ruta al archivo JSON con datos del correo (opcional)"
  )
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

  # Validar email_data si se pasa
  if args.email_data:
      if not os.path.exists(args.email_data):
          print(f"[ERROR] El archivo email_data.json no existe en: {args.email_data}")
          sys.exit(1)
      else:
          print(f"[INFO] Usando email_data.json: {args.email_data}")

  print(f"[INFO] Ejecutando script: {script_abspath}")

  # Construir comando para ejecutar el script
  cmd = [sys.executable, script_abspath, args.profile]
  if args.email_data:
      cmd.append(args.email_data)  # Pasar la ruta del JSON como tercer argumento

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
