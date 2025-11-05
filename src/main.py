import os
import sys
import platform
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

# =========================
# CONFIGURACION GENERAL
# =========================
WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
screenshots_dir = os.path.join(WORKSPACE, "screenshots")
logs_dir = os.path.join(WORKSPACE, "logs")
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
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(screenshots_dir, f"{name}_{timestamp}.png")
    driver.save_screenshot(filename)
    log("info", f"Captura guardada: {filename}")

def wait_for_loaders(driver):
    try:
        WebDriverWait(driver, DEFAULT_WAIT * 3).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".spinner, .loading, .NG-spinner"))
        )
        log("info", "Spinners de carga desaparecidos, listo para continuar.")
    except Exception:
        log("warn", "No se detectaron spinners o no desaparecieron en el tiempo esperado.")

def click_element(driver, by, value, error_message="", iframe_selector=None) -> bool:
    try:
        wait_for_loaders(driver)
        if iframe_selector:
            iframe = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, iframe_selector))
            )
            driver.switch_to.frame(iframe)
        elem = WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((by, value))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(0.5)
        elem.click()
        if iframe_selector:
            driver.switch_to.default_content()
        return True
    except Exception as e:
        log("error", f"{error_message or 'Error haciendo clic'} - {e}")
        save_screenshot(driver, f"error_click_{value}")
        driver.switch_to.default_content()
        return False

def click_shadow_element(driver, script: str, error_message="Error al acceder al elemento Shadow DOM") -> bool:
    try:
        wait_for_loaders(driver)
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

def click_btn_cert(driver) -> bool:
    try:
        wait_for_loaders(driver)
        try:
            elem = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(1)
            try:
                elem.click()
                log("info", "Botón 'btnContinuaCertCaptcha' clicado directamente en DOM principal.")
                return True
            except Exception:
                driver.execute_script("arguments[0].click();", elem)
                log("info", "Botón 'btnContinuaCertCaptcha' clicado con JavaScript en DOM principal.")
                return True
        except Exception:
            log("warn", "Botón no encontrado en DOM principal. Buscando en iframes...")

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        log("info", f"Total iframes detectados: {len(iframes)}")

        for idx, iframe in enumerate(iframes):
            driver.switch_to.frame(iframe)
            try:
                elem_iframe = WebDriverWait(driver, DEFAULT_WAIT).until(
                    EC.presence_of_element_located((By.ID, "btnContinuaCertCaptcha"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem_iframe)
                time.sleep(1)
                try:
                    elem_iframe.click()
                    log("info", f"Botón clicado correctamente en iframe {idx}.")
                    driver.switch_to.default_content()
                    return True
                except Exception:
                    driver.execute_script("arguments[0].click();", elem_iframe)
                    log("info", f"Botón clicado mediante JavaScript en iframe {idx}.")
                    driver.switch_to.default_content()
                    return True
            except Exception:
                driver.switch_to.default_content()
                continue

        log("error", "No se encontró el botón 'btnContinuaCertCaptcha' en ningún iframe.")
        return False
    except Exception as e:
        log("error", f"Error en click_btn_cert: {e}")
        save_screenshot(driver, "error_click_btn_cert")
        driver.switch_to.default_content()
        return False

def setup_driver() -> webdriver.Firefox:
    if not os.path.exists(FIREFOX_PROFILE_PATH):
        raise FileNotFoundError(f"No se encontró el perfil de Firefox en {FIREFOX_PROFILE_PATH}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
    options.profile = profile
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

# =========================
# FLUJO PRINCIPAL
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"Accediendo a: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)
        save_screenshot(driver, "01_inicio")
        WebDriverWait(driver, DEFAULT_WAIT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        log("info", "Página cargada correctamente.")
        shadow_query = (
            'return document.querySelector("#single-spa-application\\\\:mfe-main-app > app-root").'
            'shadowRoot.querySelector("main > app-acces > div > div.left > button")'
        )
        if not click_shadow_element(driver, shadow_query, "Botón 'Soc un ciutadà/ana' no encontrado"):
            return False
        save_screenshot(driver, "02_shadow_click")
        time.sleep(2)
        if not click_btn_cert(driver):
            return False
        save_screenshot(driver, "03_cert_click")
        if not click_element(driver, By.ID, "apt_did", "Elemento 'Dades i documents' no encontrado"):
            return False
        save_screenshot(driver, "04_dades_click")
        if not click_element(driver, By.XPATH, '//*[@id="center_1R"]/app-root/app-home/div/div[2]/div[2]/h3/a', "Link 'Els meus documents' no encontrado"):
            return False
        save_screenshot(driver, "05_docs_click")
        log("info", "Esperando carga final del contenido...")
        WebDriverWait(driver, DEFAULT_WAIT * 3).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
        )
        log("info", "✅ Flujo completado correctamente.")
        save_screenshot(driver, "06_final_ok")
        return True
    except Exception as e:
        log("error", f"Error en ejecución: {e}")
        save_screenshot(driver, "error_general")
        return False
    finally:
        driver.quit()
        log("info", "Driver cerrado correctamente.")

if __name__ == "__main__":
    success = run_automation()
    if not success:
        sys.exit(1)  # Esto hará que Jenkins marque el build como FAILURE
