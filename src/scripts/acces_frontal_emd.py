# =========================
# acces_frontal_emd.py
# =========================


import os
import sys
import time
import platform
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# =========================
# Cargar .env
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ACCES_FRONTAL_EMD_URL = os.getenv("ACCES_FRONTAL_EMD_URL")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "15"))

# Perfil (Jenkins o local)
FIREFOX_PROFILE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORKSPACE, "profiles", "selenium_cert")

# =========================
# Carpetas
# =========================
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

with open(os.path.join(WORKSPACE, "current_run.txt"), "w") as f:
    f.write(run_id)

# =========================
# Logging
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
    log("info", f"Captura: {filename}")
    return filename

# =========================
# Email
# =========================
def send_alert_email(screenshot_path: str, error_msg: str):
    if not EMAIL_USER or not EMAIL_PASS:
        log("warn", "Email no configurado.")
        return

    subject = "ALERTA REAL: ACCES FRONTAL EMD"
    body = f"""
    <h3>Alarma REAL detectada</h3>
    <p><strong>Error:</strong> {error_msg}</p>
    <p><strong>Run:</strong> {run_id}</p>
    <p>Revise urgentemente.</p>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    with open(screenshot_path, 'rb') as f:
        img = MIMEImage(f.read())
        img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
        msg.attach(img)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        log("info", "Email enviado.")
    except Exception as e:
        log("error", f"Email falló: {e}")

# =========================
# Driver
# =========================
def setup_driver() -> webdriver.Firefox:
  if not os.path.exists(FIREFOX_PROFILE_PATH):
      raise FileNotFoundError(f"Perfil no encontrado: {FIREFOX_PROFILE_PATH}")

  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-gpu")
  options.add_argument("--window-size=1920,1080")

  profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
  options.profile = profile

  GECKODRIVER_PATH = os.path.join(os.getenv("WORKSPACE", os.getcwd()), "bin", "geckodriver")
  service = Service(GECKODRIVER_PATH)
  driver = webdriver.Firefox(service=service, options=options)
  driver.set_page_load_timeout(60)
  return driver


# =========================
# Espera loaders
# =========================
def wait_for_loaders(driver, timeout=DEFAULT_WAIT):
    """Espera a que desaparezcan loaders, spinners y overlays."""
    loaders_selectors = [
        ".spinner", ".loading", ".loader", "[class*='spinner']", "[class*='loading']",
        "app-root[loading]", "div[id*='loader']", ".overlay", ".blocker",
        "body > div[style*='block']", "div[role='dialog']", ".modal-backdrop"
    ]
    try:
        for selector in loaders_selectors:
            try:
                WebDriverWait(driver, 2).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                )
            except:
                continue
        log("info", "Loaders/Overlays desaparecidos.")
    except:
        log("warn", "Timeout esperando loaders, pero continuamos...")

# =========================
# Clic con espera
# =========================
def click_with_wait(driver, by, selector, description, iframe=False, shadow=False):
    try:
        wait_for_loaders(driver, timeout=20)  # Más tiempo

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
                EC.presence_of_element_located((by, selector))  # Solo presence
            )
        else:
            # Esperar presencia + visibility
            elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((by, selector))
            )
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((by, selector))
            )

        # Scroll
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(1)

        # Intentar clic normal, si falla → JS
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
        with open(os.path.join(logs_dir, "status.txt"), "w") as f:
            f.write("alarma_confirmada")
        send_alert_email(screenshot, f"No se pudo interactuar: {description}")
        return False
# =========================
# Certificado (100% funcional)
# =========================
def click_btn_cert(driver) -> bool:
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
            log("warn", "Buscando en iframes...")

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
        return False
    except Exception as e:
        log("error", f"Error certificado: {e}")
        save_screenshot(driver, "error_cert")
        return False

# =========================
# Flujo principal
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"URL: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
        

        # 1. Shadow: "Soc un ciutadà/ana"
        if not click_with_wait(driver, None, None, "Botón 'Soc un ciutadà/ana'", shadow=True):
            driver.quit()
            sys.exit(1)
        

        # 2. Certificado digital
        if not click_btn_cert(driver):
            screenshot = save_screenshot(driver, "03_cert_fallo")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            send_alert_email(screenshot, "No se pudo seleccionar certificado digital")
            driver.quit()
            sys.exit(1)
        log("info", "Esperando 5 segundos extra post-certificado...")
        time.sleep(5)
        wait_for_loaders(driver, timeout=30)  # Forzar espera larga

        # 3. Dades i documents
        if not click_with_wait(driver, By.ID, "apt_did", "Dades i documents"):
            driver.quit()
            sys.exit(1)
        

        # 4. Els meus documents
        if not click_with_wait(driver, By.XPATH, '//*[@id="center_1R"]/app-root/app-home/div/div[2]/div[2]/h3/a', "Els meus documents"):
            driver.quit()
            sys.exit(1)
        

        # 5. Final: lista documentos
        log("info", "Esperando documentos...")
        try:
            WebDriverWait(driver, DEFAULT_WAIT * 2).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div'))
            )
            log("info", "FLUJOS OK - Falso positivo")
            save_screenshot(driver, "06_final_ok")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("falso_positivo")
            return True
        except:
            log("error", "ALERTA REAL: No cargaron documentos")
            screenshot = save_screenshot(driver, "alarma_real")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            send_alert_email(screenshot, "No se cargó la lista de documentos")
            return False

    except Exception as e:
        log("error", f"Error crítico: {e}")
        try:
            screenshot = save_screenshot(driver, "error_critico")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            send_alert_email(screenshot, f"Error: {e}")
        except:
            pass
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    success = run_automation()
    final_status = "falso_positivo" if success else "alarma_confirmada"
    
    # 1. En logs (para histórico)
    with open(os.path.join(logs_dir, "status.txt"), "w") as f:
        f.write(final_status)
    
    # 2. EN RAÍZ (para Jenkins)
    root_status_path = os.path.join(WORKSPACE, "status.txt")
    with open(root_status_path, "w") as f:
        f.write(final_status)
    
    if success:
        log("info", "=== JOB SUCCESS: falso_positivo ===")
        sys.exit(0)
    else:
        log("error", "=== JOB FAILURE: alarma_confirmada ===")
        sys.exit(1)