# =========================
# 01_carrega_url_wsdl.py
# =========================
"""
Script de prueba con Selenium y Firefox que:
1. Accede a la página de Google.
2. Identifica el logo de Google.
3. Si lo encuentra, toma una captura de pantalla.
4. Marca estado para Jenkins (falso_positivo o alarma_confirmada).
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

# =========================
# Cargar .env
# =========================
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
  load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())

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

  service = Service(GeckoDriverManager().install())
  driver = webdriver.Firefox(service=service, options=options)
  driver.set_page_load_timeout(60)
  return driver

# =========================
# Flujo principal
# =========================
def run_automation():
  driver = setup_driver()
  try:
      log("info", "Abriendo Google...")
      driver.get("https://www.google.com")
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
      save_screenshot(driver, "error_critico")
      return False
  finally:
      driver.quit()

# =========================
# Ejecución
# =========================
if __name__ == "__main__":
  success = run_automation()
  final_status = "falso_positivo" if success else "alarma_confirmada"

  # Guardar estado en logs
  with open(os.path.join(logs_dir, "status.txt"), "w") as f:
      f.write(final_status)

  # Guardar estado en raíz para Jenkins
  root_status_path = os.path.join(WORKSPACE, "status.txt")
  with open(root_status_path, "w") as f:
      f.write(final_status)

  if success:
      log("info", "=== JOB SUCCESS: falso_positivo ===")
      sys.exit(0)
  else:
      log("error", "=== JOB FAILURE: alarma_confirmada ===")
      sys.exit(1)
