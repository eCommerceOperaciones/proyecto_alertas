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
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JOB_NAME = os.getenv("JOB_NAME", "GSIT_alertas")
ACCES_FRONTAL_EMD_URL = os.getenv("ACCES_FRONTAL_EMD_URL")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "15"))  # Aumentado para estabilidad

# Perfil de Firefox
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
    log("info", f"Captura guardada: {filename}")
    return filename

# =========================
# Email
# =========================
def send_alert_email(screenshot_path: str, error_msg: str):
    if not EMAIL_USER or not EMAIL_PASS:
        log("warn", "Credenciales de correo no configuradas. No se enviará email.")
        return

    subject = f"ALERTA REAL: ACCES FRONTAL EMD - Revisión urgente"
    body = f"""
    <h3>Se ha detectado una <strong>alarma real</strong> en ACCES FRONTAL EMD.</h3>
    <p><strong>Detalles:</strong> {error_msg}</p>
    <p><strong>Run ID:</strong> {run_id}</p>
    <p>Por favor, revise el sistema lo antes posible.</p>
    <p><em>Este es un mensaje automático desde el monitor GSIT_alertas.</em></p>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER  # Cambia si quieres otro destinatario
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    # Adjuntar imagen
    with open(screenshot_path, 'rb') as f:
        img = MIMEImage(f.read(), name=os.path.basename(screenshot_path))
        msg.attach(img)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Cambia si usas otro servidor
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        log("info", "Email de alerta enviado correctamente.")
    except Exception as e:
        log("error", f"Error enviando email: {e}")

# =========================
# Driver
# =========================
def setup_driver() -> webdriver.Firefox:
    if not os.path.exists(FIREFOX_PROFILE_PATH):
        raise FileNotFoundError(f"Perfil de Firefox no encontrado: {FIREFOX_PROFILE_PATH}")

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
# Click con espera
# =========================
def click_with_wait(driver, by, selector, description, timeout=DEFAULT_WAIT, shadow=False):
    try:
        if shadow:
            script = f"""
            return document.querySelector("#single-spa-application\\\\:mfe-main-app > app-root")
                .shadowRoot.querySelector("main > app-acces > div > div.left > button");
            """
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script(script) is not None
            )
            element = driver.execute_script(script)
        else:
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element = driver.find_element(by, selector)

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        log("info", f"✓ Clic en: {description}")
        return True
    except Exception as e:
        log("error", f"✗ No se encontró o no clickable: {description} | Error: {e}")
        screenshot = save_screenshot(driver, f"error_{description.replace(' ', '_')}")
        with open(os.path.join(logs_dir, "status.txt"), "w") as f:
            f.write("alarma_confirmada")
        send_alert_email(screenshot, f"Falló al hacer clic en: {description}")
        return False

# =========================
# Flujo principal
# =========================
def run_automation():
    driver = setup_driver()
    try:
        log("info", f"Accediendo a: {ACCES_FRONTAL_EMD_URL}")
        driver.get(ACCES_FRONTAL_EMD_URL)

        WebDriverWait(driver, DEFAULT_WAIT * 3).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        log("info", "Página cargada completamente.")

        # 1. Botón "Soc un ciutadà/ana" (Shadow DOM)
        if not click_with_wait(
            driver=driver,
            by=None,
            selector=None,
            description="Botón 'Soc un ciutadà/ana'",
            shadow=True
        ):
            driver.quit()
            sys.exit(1)

        # 2. "Dades i documents" (ID: apt_did)
        if not click_with_wait(
            driver=driver,
            by=By.ID,
            selector="apt_did",
            description="Elemento 'Dades i documents'"
        ):
            driver.quit()
            sys.exit(1)

        # 3. Link "Els meus documents"
        if not click_with_wait(
            driver=driver,
            by=By.XPATH,
            selector='//*[@id="center_1R"]/app-root/app-home/div/div[2]/div[2]/h3/a',
            description="Link 'Els meus documents'"
        ):
            driver.quit()
            sys.exit(1)

        save_screenshot(driver, "05_docs_click")

        # 4. Esperar contenido final: lista de documentos
        log("info", "Esperando carga final del contenido...")
        try:
            WebDriverWait(driver, DEFAULT_WAIT * 3).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="center_1R"]/app-root/app-emd/emd-home/emd-documents/div/emd-cards-view/ul/li[1]/div')
                )
            )
            log("info", "✅ Flujo completado correctamente.")
            final_screenshot = save_screenshot(driver, "06_final_ok")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("falso_positivo")
            return True
        except Exception as e:
            log("error", "Alarma ACCES FRONTAL EMD confirmada: no se cargaron los documentos.")
            screenshot = save_screenshot(driver, "alarma_confirmada")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            send_alert_email(screenshot, "No se cargó la lista de documentos. Alarma real.")
            return False

    except Exception as e:
        log("error", f"Error general en ejecución: {e}")
        try:
            screenshot = save_screenshot(driver, "error_general")
            with open(os.path.join(logs_dir, "status.txt"), "w") as f:
                f.write("alarma_confirmada")
            send_alert_email(screenshot, f"Error crítico: {e}")
        except:
            pass
        return False
    finally:
        driver.quit()
        log("info", "Driver cerrado.")

if __name__ == "__main__":
    success = run_automation()
    sys.exit(0 if success else 1)