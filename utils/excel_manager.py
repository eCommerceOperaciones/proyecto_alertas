import os
import pandas as pd
from datetime import datetime

# 📌 Ruta compartida para todos los Jobs
EXCEL_PATH = "/var/lib/jenkins/shared/alertas.xlsx"

def ensure_shared_excel_dir():
  """Crea el directorio compartido si no existe y da permisos."""
  shared_dir = os.path.dirname(EXCEL_PATH)
  if not os.path.exists(shared_dir):
      os.makedirs(shared_dir, exist_ok=True)
  # Dar permisos de lectura/escritura a todos los usuarios de Jenkins
  try:
      os.chmod(shared_dir, 0o777)
  except Exception as e:
      print(f"[WARN] No se pudieron cambiar permisos del directorio: {e}")

def create_excel_if_not_exists():
  """Crea el Excel si no existe."""
  ensure_shared_excel_dir()
  if not os.path.exists(EXCEL_PATH):
      df = pd.DataFrame(columns=[
          "ID", "Inici", "Fi", "Afecta a", "Incidència", "Parcial/Total", "Origen", "Descripción"
      ])
      df.to_excel(EXCEL_PATH, index=False)
      try:
          os.chmod(EXCEL_PATH, 0o666)  # Permisos lectura/escritura
      except Exception as e:
          print(f"[WARN] No se pudieron cambiar permisos del Excel: {e}")
      print(f"[INFO] Excel creado en {EXCEL_PATH}")

def add_alert(fields):
  """Añade una nueva alerta al Excel."""
  create_excel_if_not_exists()
  df = pd.read_excel(EXCEL_PATH)
  df = pd.concat([df, pd.DataFrame([fields])], ignore_index=True)
  df.to_excel(EXCEL_PATH, index=False)
  print(f"[INFO] Alerta añadida con ID {fields['ID']}")

def close_alert(fields):
  """Cierra una alerta existente actualizando la columna Fi."""
  create_excel_if_not_exists()
  df = pd.read_excel(EXCEL_PATH)
  match = df[df["ID"] == fields["ID"]]
  if not match.empty:
      df.loc[df["ID"] == fields["ID"], "Fi"] = fields["Fi"] or datetime.now().strftime("%d/%m/%Y %H:%M")
      df.to_excel(EXCEL_PATH, index=False)
      print(f"[INFO] Alerta {fields['ID']} cerrada correctamente.")
  else:
      print(f"[ERROR] No se encontró alerta con ID {fields['ID']}")
