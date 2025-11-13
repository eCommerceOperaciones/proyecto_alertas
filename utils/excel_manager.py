import os
import pandas as pd
from datetime import datetime

# Ruta compartida para todos los Jobs
SHARED_EXCEL_PATH = "/var/lib/jenkins/shared/alertas.xlsx"

def ensure_shared_excel_dir():
   """Crea el directorio compartido si no existe y da permisos."""
   shared_dir = os.path.dirname(SHARED_EXCEL_PATH)
   if not os.path.exists(shared_dir):
       os.makedirs(shared_dir, exist_ok=True)
   try:
       os.chmod(shared_dir, 0o777)
   except Exception as e:
       print(f"[WARN] No se pudieron cambiar permisos del directorio: {e}")

def create_excel_if_not_exists():
   """Crea el Excel si no existe en la ruta compartida."""
   ensure_shared_excel_dir()
   if not os.path.exists(SHARED_EXCEL_PATH):
       df = pd.DataFrame(columns=[
           "ID", "Inici", "Fi", "Afecta a", "Incidència", "Parcial/Total", "Origen", "Descripción"
       ])
       df.to_excel(SHARED_EXCEL_PATH, index=False)
       try:
           os.chmod(SHARED_EXCEL_PATH, 0o666)
       except Exception as e:
           print(f"[WARN] No se pudieron cambiar permisos del Excel: {e}")
       print(f"[INFO] Excel creado en {SHARED_EXCEL_PATH}")
   else:
       print(f"[INFO] Usando Excel existente en {SHARED_EXCEL_PATH}")

def add_alert(fields):
   """Añade una nueva alerta al Excel compartido evitando duplicados."""
   create_excel_if_not_exists()
   df = pd.read_excel(SHARED_EXCEL_PATH)

   alert_id = str(fields.get("ID")).strip()
   if alert_id in df["ID"].astype(str).str.strip().values:
       print(f"[INFO] ALERT_ID {alert_id} ya existe en Excel, no se añade duplicado.")
       return

   df = pd.concat([df, pd.DataFrame([fields])], ignore_index=True)
   df.to_excel(SHARED_EXCEL_PATH, index=False)
   print(f"[INFO] Alerta añadida con ID {alert_id}")

def close_alert(fields):
   """Cierra una alerta existente actualizando la columna Fi."""
   create_excel_if_not_exists()
   df = pd.read_excel(SHARED_EXCEL_PATH)
   alert_id = str(fields.get("ID")).strip()
   match = df[df["ID"].astype(str).str.strip() == alert_id]
   if not match.empty:
       df.loc[df["ID"].astype(str).str.strip() == alert_id, "Fi"] = fields.get("Fi") or datetime.now().strftime("%d/%m/%Y %H:%M")
       df.to_excel(SHARED_EXCEL_PATH, index=False)
       print(f"[INFO] Alerta {alert_id} cerrada correctamente.")
   else:
       print(f"[ERROR] No se encontró alerta con ID {alert_id}")
