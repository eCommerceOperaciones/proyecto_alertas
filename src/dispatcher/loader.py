# src/dispatcher/loader.py
from dispatcher.registry import SCRIPT_REGISTRY




def load_script_path(alert_name: str) -> str:
    """Devuelve la ruta relativa del script asociado al alert_name.


    Lanza ValueError si el script no está registrado.
    """
    key = alert_name.lower().strip()
    if key not in SCRIPT_REGISTRY:
        raise ValueError(f"Script '{alert_name}' no está registrado. Disponibles: {list(SCRIPT_REGISTRY.keys())}")
    return SCRIPT_REGISTRY[key]