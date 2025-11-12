# utils/excel_manager.py
import os
import pandas as pd
from datetime import datetime

EXCEL_PATH = os.path.join(os.getcwd(), "alertas.xlsx")

def create_excel_if_not_exists():
    """Crea el Excel si no existe."""
    if not os.path.exists(EXCEL_PATH):
        df = pd.DataFrame(columns=[
            "ID", "Inici", "Fi", "Afecta a", "Incidència", "Parcial/Total", "Origen", "Descripción"
        ])
        df.to_excel(EXCEL_PATH, index=False)
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
