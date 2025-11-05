import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

# =========================
# CONFIGURACIÓN DE CARPETAS POR EJECUCIÓN
# =========================
WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

FIREFOX_PROFILE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORKSPACE, "profiles", "selenium_cert")
ACCES_FRONTAL_EMD_URL = "https://ovt.gencat.cat/carpetaciutadana360/mfe-main-app/#/acces?set-locale=ca_ES"
DEFAULT_WAIT = 10

# =========================
# FUNCIONES AUXILIARES
# =========================
def log(level: str, message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level.upper()}] {message}"
    print(line)
    with open(os.path.join(logs_dir, "execution.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def save_screenshot(driver, name: str) -> None:
    filename = os.path.join(screenshots_dir, f"{name}.png")
    driver.save_screenshot(filename)
    log("info", f"Captura guardada: {filename}")

def setup_driver() -> webdriver.Firefox:
    if not os.path.exists(FIREFOX_PROFILE_PATH):
        raise FileNotFoundError(f"No se encontró el perfil de Firefox en {FIREFOX_PROFILE_PATH}")
    options = Options()
    options.add_argument("--headless")
    profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
    options.profile = profile
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

# =========================
# FLUJO PRINCIPAL CON REINTENTO
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"Accediendo a: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)
        WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        log("info", "Página cargada correctamente.")

        # Aquí iría el resto del flujo Selenium...
        # Último elemento
        try:
            WebDriverWait(driver, DEFAULT_WAIT * 3).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
            )
            log("info", "✅ Flujo completado correctamente.")
            save_screenshot(driver, "final_ok")
            return True
        except Exception:
            log("warn", "Falso positivo detectado, reintentando en 5 minutos...")
            driver.quit()
            time.sleep(300)  # Espera 5 minutos
            return retry_automation()

    except Exception as e:
        log("error", f"Error en ejecución: {e}")
        save_screenshot(driver, "error_general")
        return False
    finally:
        driver.quit()
        log("info", "Driver cerrado correctamente.")

def retry_automation():
    driver = setup_driver()
    try:
        log("info", "Reintento de flujo...")
        driver.get(ACCES_FRONTAL_EMD_URL)
        WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            WebDriverWait(driver, DEFAULT_WAIT * 3).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
            )
            log("info", "✅ Elemento encontrado en reintento.")
            save_screenshot(driver, "final_ok_retry")
            return True
        except Exception:
            log("error", "Elemento no encontrado tras reintento.")
            save_screenshot(driver, "error_final")
            return False
    finally:
        driver.quit()
        log("info", "Driver cerrado tras reintento.")

if __name__ == "__main__":
    success = run_automation()
    if not success:
        sys.exit(1)
