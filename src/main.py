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
# Cargar .env solo como respaldo
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_alertas")
ACCES_FRONTAL_EMD_URL = os.getenv("ACCES_FRONTAL_EMD_URL")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "10"))

# ✅ CORRECCION: Inicializar FIREFOX_PROFILE_PATH
FIREFOX_PROFILE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORKSPACE, "profiles", "selenium_cert")

# =========================
# Carpetas por ejecución
# =========================
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Guardar run_id para que Jenkins lo use
with open(os.path.join(WORKSPACE, "current_run.txt"), "w") as f:
    f.write(run_id)

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

def click_shadow_element(driver, script: str, error_message="Error al acceder al elemento Shadow DOM") -> bool:
    try:
        element = driver.execute_script(script)
        if not element:
            raise ValueError("Elemento Shadow DOM no encontrado")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        return True
    except Exception as e:
        log("error", f"{error_message} - {e}")
        save_screenshot(driver, "error_shadow")
        return False

def click_element(driver, by, value, description) -> bool:
    try:
        WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.visibility_of_element_located((by, value))
        )
        WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((by, value))
        )
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

def click_btn_cert(driver) -> bool:
    try:
        elem = WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(1)
        elem.click()
        log("info", "Botón 'btnContinuaCertCaptcha' clicado.")
        return True
    except Exception:
        log("warn", "Botón no encontrado en DOM principal. Buscando en iframes...")
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.frame(iframe)
            try:
                elem_iframe = WebDriverWait(driver, DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem_iframe)
                time.sleep(1)
                elem_iframe.click()
                log("info", "Botón clicado en iframe.")
                driver.switch_to.default_content()
                return True
            except Exception:
                driver.switch_to.default_content()
                continue
        return False

# =========================
# Flujo principal
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"Accediendo a: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)

        # Espera a que el DOM esté completamente cargado
        WebDriverWait(driver, DEFAULT_WAIT * 3).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        log("info", "Página cargada y DOM listo.")

        WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        log("info", "Página cargada correctamente.")

        shadow_query = (
            'return document.querySelector("#single-spa-application\\\\:mfe-main-app > app-root").'
            'shadowRoot.querySelector("main > app-acces > div > div.left > button")'
        )
        if not click_shadow_element(driver, shadow_query, "Botón 'Soc un ciutadà/ana' no encontrado"):
            return False

        time.sleep(2)

        if not click_btn_cert(driver):
            return False

        if not click_element(driver, By.ID, "apt_did", "Elemento 'Dades i documents' no encontrado"):
            return False

        if not click_element(driver, By.XPATH, '//*[@id="center_1R"]/app-root/app-home/div/div[2]/div[2]/h3/a', "Link 'Els meus documents' no encontrado"):
            return False
        save_screenshot(driver, "05_docs_click")

        log("info", "Esperando carga final del contenido...")
        try:
            WebDriverWait(driver, DEFAULT_WAIT * 3).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
            )
            log("info", "✅ Flujo completado correctamente.")
            save_screenshot(driver, "06_final_ok")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("falso_positivo")
            return True
        except Exception:
            log("error", "Alarma ACCES FRONTAL EMD confirmada")
            save_screenshot(driver, "alarma_confirmada")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            return False

    except Exception as e:
        log("error", f"Error en ejecución: {e}")
        save_screenshot(driver, "error_general")
        with open(os.path.join(logs_dir, "status.txt"), "w") as f:
            f.write("alarma_confirmada")
        return False
    finally:
        driver.quit()
        log("info", "Driver cerrado correctamente.")

if __name__ == "__main__":
    success = run_automation()
    sys.exit(0 if success else 1)
