import os
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

DEFAULT_WAIT = 30
URL = "https://ovt.gencat.cat/carpetaciutadana360/mfe-main-app/#/acces?set-locale=ca_ES"
PROFILE_PATH = "/home/seluser/firefox-profile"


def log(level, msg):
    print(f"[{level.upper()}] {msg}", flush=True)


def save_screenshot(driver, name):
    path = f"/home/seluser/output/{name}.png"
    driver.save_screenshot(path)
    log("info", f"Captura guardada: {path}")
    return path


def verify_profile_and_cert():
    """Verifica que el perfil existe y que el certificado está importado."""
    if not os.path.exists(PROFILE_PATH):
        log("error", f"Perfil {PROFILE_PATH} no existe.")
        return False

    files = os.listdir(PROFILE_PATH)
    log("info", f"Archivos en el perfil: {files}")

    try:
        result = subprocess.run(
            ["certutil", "-L", "-d", f"sql:{PROFILE_PATH}"],
            capture_output=True, text=True
        )
        log("info", f"Certificados en el perfil:\n{result.stdout}")

        # Detectamos cualquier certificado con trust "u,u,u" o similar
        if "u,u,u" in result.stdout:
            log("info", "✓ Certificado personal detectado.")
            return True
        else:
            log("error", "❌ No se detectó certificado personal en el perfil.")
            return False

    except Exception as e:
        log("error", f"No se pudo verificar el certificado: {e}")
        return False


def wait_for_loaders(driver, timeout=DEFAULT_WAIT):
    loaders_selectors = [
        ".spinner", ".loading", ".loader",
        "[class*='spinner']", "[class*='loading']",
        "app-root[loading]", "div[id*='loader']",
        ".overlay", ".blocker",
        "body > div[style*='block']",
        ".modal-backdrop"
    ]

    for selector in loaders_selectors:
        try:
            WebDriverWait(driver, 2).until(
                EC.invisibility_of_element_located(("css selector", selector))
            )
        except:
            continue

    log("info", "Loaders/Overlays desaparecidos.")


def click_with_wait(driver, description, by=None, selector=None, shadow=False):
    try:
        wait_for_loaders(driver, timeout=20)

        if shadow:
            script = (
                'return document.querySelector("#single-spa-application\\\\:mfe-main-app > app-root")'
                '.shadowRoot.querySelector("main > app-acces > div > div.left > button")'
            )
            WebDriverWait(driver, DEFAULT_WAIT).until(lambda d: d.execute_script(script))
            elem = driver.execute_script(script)
        else:
            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.element_to_be_clickable((by, selector))
            )
            elem = driver.find_element(by, selector)

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(1)

        try:
            elem.click()
            log("info", f"✓ Clic normal: {description}")
        except:
            log("warn", f"Clic normal falló, usando JS para: {description}")
            driver.execute_script("arguments[0].click();", elem)
            log("info", f"✓ Clic con JS: {description}")

        return True

    except Exception as e:
        log("error", f"✗ Fallo total: {description} | {e}")
        save_screenshot(driver, f"error_{description.replace(' ', '_')}")
        return False


def main():

    # Crear carpeta de capturas
    os.makedirs("/home/seluser/output", exist_ok=True)

    # 1️⃣ Verificar perfil y certificado ANTES de arrancar Firefox
    if not verify_profile_and_cert():
        log("error", "Perfil incompleto o certificado no importado. Abortando.")
        return

    # 2️⃣ Preparar Firefox con el perfil correcto
    log("info", "Inicializando Firefox con perfil...")
    profile = FirefoxProfile(PROFILE_PATH)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.profile = profile

    service = Service("/usr/local/bin/geckodriver")
    driver = webdriver.Firefox(service=service, options=options)

    try:
        log("info", f"Abrir URL: {URL}")
        driver.get(URL)

        WebDriverWait(driver, DEFAULT_WAIT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        save_screenshot(driver, "paso1_inicial")

        # Paso 1: botón "Soc un ciutadà"
        if not click_with_wait(driver, "Botón 'Soc un ciutadà/ana'", shadow=True):
            driver.quit()
            return

        time.sleep(2)
        save_screenshot(driver, "paso2_despues_click_ciutada")

        # Paso 2: botón "Continuar con certificado"
        if not click_with_wait(driver, "Botón 'Continuar con certificado'",
                               By.ID, "btnContinuaCertCaptcha"):
            driver.quit()
            return

        time.sleep(2)
        save_screenshot(driver, "paso3_despues_click_cert")

    finally:
        driver.quit()
        log("info", "Navegador cerrado correctamente.")


if __name__ == "__main__":
    main()
