import json
from pathlib import Path
import pandas as pd
from loguru import logger

# Ruta del archivo Excel (puede estar en el volumen o en un path compartido)
excel_path = Path("/app/credentials/control_alertas.xlsx")

# Ruta de archivo temporal con datos de la alerta procesada
alerta_data_path = Path("/app/credentials/alerta_procesada.json")

def actualizar_excel():
    try:
        if not excel_path.exists():
            logger.warning("El archivo Excel no existe, creando uno nuevo...")
            df = pd.DataFrame(columns=["ID", "Tipo", "Estado", "Fecha", "Detalles"])
        else:
            df = pd.read_excel(excel_path)

        with open(alerta_data_path) as f:
            alerta_data = json.load(f)

        # Buscar si la alerta ya existe en el Excel
        idx = df.index[df["ID"] == alerta_data["id"]].tolist()
        if idx:
            # Actualizar fila existente
            df.loc[idx[0], "Estado"] = alerta_data["estado"]
            df.loc[idx[0], "Fecha"] = alerta_data["fecha"]
            df.loc[idx[0], "Detalles"] = alerta_data["detalles"]
            logger.info(f"Alerta {alerta_data['id']} actualizada en Excel.")
        else:
            # Insertar nueva fila
            df = pd.concat([df, pd.DataFrame([alerta_data])], ignore_index=True)
            logger.info(f"Alerta {alerta_data['id']} añadida al Excel.")

        df.to_excel(excel_path, index=False)
        logger.info("Excel guardado correctamente.")

    except Exception as e:
        logger.error(f"Error actualizando Excel: {e}")
        raise

if __name__ == "__main__":
    logger.info("Iniciando actualización de Excel...")
    actualizar_excel()
