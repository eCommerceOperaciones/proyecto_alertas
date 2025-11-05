import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

# =========================
# Cargar configuración
# =========================
load_dotenv()
WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
ACCES_FRONTAL_EMD_URL = os.getenv("ACCES_FRONTAL_EMD_URL", "https://example.com")
FIREFOX_PROFILE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORKSPACE, "profiles", "selenium_cert")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "10"))

# =========================
# Carpetas por ejecución
# =========================
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# =========================
# Funciones auxiliares
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

def wait_and_click(driver, by, value, description):
    try:
        WebDriverWait(driver, DEFAULT_WAIT).until(EC.element_to_be_clickable((by, value)))
        elem = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(0.5)
        elem.click()
        log("info", f"Clic en {description}")
        return True
    except Exception as e:
        log("error", f"No se pudo hacer clic en {description}: {e}")
        save_screenshot(driver, f"error_click_{description}")
        return False

def check_element(driver) -> bool:
    try:
        WebDriverWait(driver, DEFAULT_WAIT * 3).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
        )
        return True
    except Exception:
        return False

# =========================
# Flujo principal
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"Accediendo a: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)
        WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        log("info", "Página cargada correctamente.")

        # Aquí irían los pasos intermedios con wait_and_click(...)
        # Ejemplo:
        # wait_and_click(driver, By.ID, "btnContinuaCertCaptcha", "Botón Continuar")

        if check_element(driver):
            log("warn", "Alarma ACCES FRONTAL EMD falso positivo")
            save_screenshot(driver, "falso_positivo")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("falso_positivo")
            return True
        else:
            log("error", "Alarma ACCES FRONTAL EMD confirmada")
            save_screenshot(driver, "alarma_confirmada")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            return False

    finally:
        driver.quit()
        log("info", "Driver cerrado correctamente.")

if __name__ == "__main__":
    success = run_automation()
    sys.exit(0 if success else 1)
