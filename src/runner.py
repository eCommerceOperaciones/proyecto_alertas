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
    args = parser.parse_args()

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

    # Ejecutar el script como subproceso usando el mismo intérprete
    cmd = [sys.executable, script_abspath, args.profile]
    try:
        proc = subprocess.run(cmd, check=False)
        rc = proc.returncode
        print(f"[INFO] Proceso finalizado con código: {rc}")
    except Exception as e:
        print(f"[ERROR] Fallo al ejecutar el script: {e}")
        rc = 1

    # Leer status.txt que crea el script (debe existir)
    status_file = os.path.join(WORKSPACE, "status.txt")
    status = None
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                status = f.read().strip()
        except Exception as e:
            print(f"[WARN] No se pudo leer status.txt: {e}")

    # Si el script devuelve 0 y el status es falso_positivo -> success
    if status:
        print(f"[INFO] status.txt => {status}")
    else:
        print("[WARN] status.txt no encontrado o vacío")

    # Salida: 0 si éxito (falso_positivo), 1 si alarma_confirmada o error
    if status == "falso_positivo":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()