import os
import sys
import time
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

# =========================
# Cargar .env
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
  load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
ALERT_NAME = sys.argv[2] if len(sys.argv) > 2 else ""
FROM_EMAIL = sys.argv[3] if len(sys.argv) > 3 else ""
EMAIL_SUBJECT = sys.argv[4] if len(sys.argv) > 4 else ""
EMAIL_BODY = sys.argv[5] if len(sys.argv) > 5 else ""

# =========================
# Carpetas
# =========================
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(WORKSPACE, "runs", run_id)
screenshots_dir = os.path.join(run_dir, "screenshots")
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

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

def write_status(status_value):
  with open(os.path.join(logs_dir, "status.txt"), "w") as f:
      f.write(status_value)
  with open(os.path.join(WORKSPACE, "status.txt"), "w") as f:
      f.write(status_value)

# =========================
# Driver con webdriver-manager y perfil temporal
# =========================
def setup_driver() -> webdriver.Firefox:
  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-gpu")
  options.add_argument("--window-size=1920,1080")
  temp_profile_path = tempfile.mkdtemp()
  options.profile = webdriver.FirefoxProfile(temp_profile_path)
  service = Service(GeckoDriverManager().install())
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
      driver.get("https://www.google.com")
      time.sleep(2)
      try:
          logo = driver.find_element(By.ID, "hplogo")
      except NoSuchElementException:
          try:
              logo = driver.find_element(By.XPATH, "//img[@alt='Google']")
          except NoSuchElementException:
              logo = None
      if logo:
          log("info", "Logo encontrado → alarma_confirmada")
          save_screenshot(driver, "google_logo")
          write_status("alarma_confirmada")
          return False
      else:
          log("info", "Logo NO encontrado → falso_positivo")
          save_screenshot(driver, "logo_no_encontrado")
          write_status("falso_positivo")
          return True
  except Exception as e:
      log("error", f"Error crítico: {e}")
      if driver:
          save_screenshot(driver, "error_critico")
      write_status("alarma_confirmada")
      return False
  finally:
      if driver:
          driver.quit()

if __name__ == "__main__":
  log("info", f"Alerta: {ALERT_NAME} | Remitente: {FROM_EMAIL} | Asunto: {EMAIL_SUBJECT}")
  success = run_automation()
  sys.exit(0)  # Jenkins decide si reintenta o no
