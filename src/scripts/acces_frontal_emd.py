"""
Script de automatización Selenium para validar el acceso frontal EMD.
Este script:
1. Carga configuración desde .env y variables de entorno.
2. Abre un navegador Firefox con perfil preconfigurado.
3. Realiza pasos de autenticación y navegación en la web objetivo.
4. Detecta si la alerta es un falso positivo o una alerta real.
5. Guarda capturas, logs y estado de la ejecución en archivos.
6. NO envía correos (la notificación se gestiona en Jenkins).
Autor: Rodrigo Simoes
Proyecto: GSIT_Alertas
"""
import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service

# =========================
# Cargar configuración
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
ACCES_FRONTAL_EMD_URL = os.getenv("ACCES_FRONTAL_EMD_URL")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "15"))
ALERT_ID = os.getenv("ALERT_ID", datetime.now().strftime("%Y%m%d_%H%M%S"))
ALERT_NAME = os.getenv("ALERT_NAME", "Acces Frontal EMD")

# =========================
# Carpetas de ejecución
# =========================
run_dir = os.path.join(WORKSPACE, "runs", ALERT_ID)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# =========================
# Logging y utilidades
# =========================
def log(level: str, message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level.upper()}] {message}"
    print(line)
    with open(os.path.join(logs_dir, "execution.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def save_screenshot(driver, name: str) -> str:
    filename = os.path.join(screenshots_dir, f"{name}.png")
    driver.save_screenshot(filename)
    log("info", f"Captura guardada en: {filename}")
    return filename

def write_status(status_value):
    log("info", f"Escribiendo status: {status_value}")
    with open(os.path.join(logs_dir, "status.txt"), "w") as f:
        f.write(status_value)
    with open(os.path.join(WORKSPACE, "status.txt"), "w") as f:
        f.write(status_value)

def save_result(status, error_message=None, screenshots=None):
    result = {
        "status": status,
        "alert_id": ALERT_ID,
        "alert_name": ALERT_NAME,
        "error_message": error_message,
        "screenshots": screenshots or [],
        "logs": ["execution.log"]
    }
    with open(os.path.join(WORKSPACE, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

# =========================
# Driver Selenium
# =========================
def setup_driver() -> webdriver.Firefox:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    options = Options()
    # NO necesitas perfil, NO necesitas sandbox, NO necesitas nada más
    driver = webdriver.Remote(
        command_executor="http://selenium-firefox:4444/wd/hub",
        options=options
    )
    driver.set_page_load_timeout(60)
    log("info", "Conectado al nodo Selenium Firefox → TODO AUTOMÁTICO")
    return driver

# =========================
# Funciones de interacción
# =========================
def wait_for_loaders(driver, timeout=DEFAULT_WAIT):
    loaders_selectors = [
        ".spinner", ".loading", ".loader", "[class*='spinner']", "[class*='loading']",
        "app-root[loading]", "div[id*='loader']", ".overlay", ".blocker",
        "body > div[style*='block']", "div[role='dialog']", ".modal-backdrop"
    ]
    for selector in loaders_selectors:
        try:
            WebDriverWait(driver, 2).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
            )
        except:
            continue
    log("info", "Loaders/Overlays desaparecidos.")

def click_with_wait(driver, by, selector, description, iframe=False, shadow=False):
    try:
        wait_for_loaders(driver, timeout=20)
        if shadow:
            script = 'return document.querySelector("#single-spa-application\\\\:mfe-main-app > app-root").shadowRoot.querySelector("main > app-acces > div > div.left > button")'
            WebDriverWait(driver, DEFAULT_WAIT).until(lambda d: d.execute_script(script))
            elem = driver.execute_script(script)
        elif iframe:
            iframe_elem = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            driver.switch_to.frame(iframe_elem)
            elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((by, selector))
            )
        else:
            elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((by, selector))
            )
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((by, selector))
            )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(1)
        try:
            elem.click()
            log("info", f"✓ Clic normal: {description}")
        except:
            log("warn", f"Clic normal falló, usando JS para: {description}")
            driver.execute_script("arguments[0].click();", elem)
            log("info", f"✓ Clic con JS: {description}")
        if iframe:
            driver.switch_to.default_content()
        return True
    except Exception as e:
        log("error", f"✗ Fallo total: {description} | {e}")
        screenshot = save_screenshot(driver, f"error_{description.replace(' ', '_')}")
        write_status("alarma_confirmada")
        save_result("alarma_confirmada", f"No se pudo interactuar: {description}", [os.path.basename(screenshot)])
        return False

def click_btn_cert(driver) -> bool:
    """
    Intenta hacer clic en el botón de certificado digital, buscando en DOM principal e iframes.
    """
    try:
        wait_for_loaders(driver)
        try:
            elem = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", elem)
            log("info", "Certificado clicado (DOM principal).")
            return True
        except:
            log("warn", "Buscando certificado en iframes...")

        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.frame(iframe)
            try:
                elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
                )
                driver.execute_script("arguments[0].click();", elem)
                log("info", "Certificado clicado en iframe.")
                driver.switch_to.default_content()
                return True
            except:
                driver.switch_to.default_content()

        log("error", "No se encontró el botón de certificado digital.")
        screenshot = save_screenshot(driver, "cert_fallo")
        write_status("alarma_confirmada")
        save_result("alarma_confirmada", "No se pudo seleccionar certificado digital", [os.path.basename(screenshot)])
        return False

    except Exception as e:
        log("error", f"Error certificado: {e}")
        screenshot = save_screenshot(driver, "error_cert")
        write_status("alarma_confirmada")
        save_result("alarma_confirmada", f"Error certificado: {e}", [os.path.basename(screenshot)])
        return False

# =========================
# Flujo principal
# =========================
def run_automation():
    driver = setup_driver()
    time.sleep(3)  # ← Da tiempo al perfil a cargarse completamente
    log("info", "Esperando 3 segundos para que el perfil se cargue...")
    try:
        log("info", f"URL: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")

        if not click_with_wait(driver, None, None, "Botón 'Soc un ciutadà/ana'", shadow=True):
            driver.quit()
            return False

        if not click_btn_cert(driver):
            driver.quit()
            return False

        log("info", "Esperando 5 segundos extra post-certificado...")
        time.sleep(5)
        wait_for_loaders(driver, timeout=30)

        if not click_with_wait(driver, By.ID, "apt_did", "Dades i documents"):
            driver.quit()
            return False

        if not click_with_wait(driver, By.XPATH, '//*[@id="center_1R"]/app-root/app-home/div/div[2]/div[2]/h3/a', "Els meus documents"):
            driver.quit()
            return False

        log("info", "Esperando documentos...")
        try:
            WebDriverWait(driver, DEFAULT_WAIT * 2).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
            )
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'spinner') or contains(@class, 'loading') or contains(@class, 'overlay')]")
                )
            )
            log("info", "FLUJOS OK - Falso positivo")
            screenshot = save_screenshot(driver, "final_ok")
            write_status("falso_positivo")
            save_result("falso_positivo", None, [os.path.basename(screenshot)])
            return True
        except:
            log("error", "ALERTA REAL: No cargaron documentos")
            screenshot = save_screenshot(driver, "alarma_real")
            write_status("alarma_confirmada")
            save_result("alarma_confirmada", "No se cargó la lista de documentos", [os.path.basename(screenshot)])
            return False

    except Exception as e:
        log("error", f"Error crítico: {e}")
        screenshot = save_screenshot(driver, "error_critico")
        write_status("alarma_confirmada")
        save_result("alarma_confirmada", f"Error crítico: {e}", [os.path.basename(screenshot)])
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    success = run_automation()
    sys.exit(0 if success else 1)
