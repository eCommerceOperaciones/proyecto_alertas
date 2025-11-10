# =========================
# 01_carrega_url_wsdl.py (adaptado sin JSON)
# =========================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException
import os, sys, time
from datetime import datetime
from dotenv import load_dotenv

# =========================
# Cargar .env
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
  load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())

# Argumentos esperados:
# sys.argv[1] -> perfil selenium
# sys.argv[2] -> alert_name
# sys.argv[3] -> from_email
# sys.argv[4] -> subject
# sys.argv[5] -> body
FIREFOX_PROFILE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORKSPACE, "profiles", "selenium_cert")
ALERT_NAME = sys.argv[2] if len(sys.argv) > 2 else ""
FROM_EMAIL = sys.argv[3] if len(sys.argv) > 3 else ""
EMAIL_SUBJECT = sys.argv[4] if len(sys.argv) > 4 else ""
EMAIL_BODY = sys.argv[5] if len(sys.argv) > 5 else ""

# =========================
# Carpetas y run_id
# =========================
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Guardar run_id para Jenkins
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
# Mostrar datos del correo
# =========================
def print_email_data():
  log("info", "=== Datos del correo que disparó la alerta ===")
  log("info", f"Alerta: {ALERT_NAME}")
  log("info", f"Remitente: {FROM_EMAIL}")
  log("info", f"Asunto: {EMAIL_SUBJECT}")
  log("info", f"Cuerpo: {EMAIL_BODY}")

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

  GECKODRIVER_PATH = os.path.join(WORKSPACE, "bin", "geckodriver")
  service = Service(GECKODRIVER_PATH)
  driver = webdriver.Firefox(service=service, options=options)
  driver.set_page_load_timeout(60)
  return driver

# =========================
# Flujo principal
# =========================
def run_automation():
  driver = None
  try:
      driver = setup_driver()
      log("info", "Abriendo Google...")
      driver.get("bloqueado")
      time.sleep(2)

      log("info", "Buscando el logo de Google...")
      try:
          logo = driver.find_element(By.ID, "hplogo")
      except NoSuchElementException:
          try:
              logo = driver.find_element(By.XPATH, "//img[@alt='Google']")
          except NoSuchElementException:
              logo = None

      if logo:
          log("info", "Logo encontrado. Tomando captura...")
          save_screenshot(driver, "google_logo")
          return True
      else:
          log("error", "Logo no encontrado.")
          save_screenshot(driver, "logo_no_encontrado")
          return False

  except Exception as e:
      log("error", f"Error crítico: {e}")
      if driver:
          save_screenshot(driver, "error_critico")
      return False
  finally:
      if driver:
          driver.quit()

if __name__ == "__main__":
  # Mostrar datos del correo al inicio
  print_email_data()

  success = run_automation()
  final_status = "falso_positivo" if success else "alarma_confirmada"

  # Guardar status en logs y raíz para Jenkins
  with open(os.path.join(logs_dir, "status.txt"), "w") as f:
      f.write(final_status)
  with open(os.path.join(WORKSPACE, "status.txt"), "w") as f:
      f.write(final_status)

  sys.exit(0 if success else 1)
