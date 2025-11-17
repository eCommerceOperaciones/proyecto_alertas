# src/scripts/area_privada.py
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
ENV_PATH = os.path.join(os.getcwd(), ".env")
if os.path.exists(ENV_PATH):
  load_dotenv(dotenv_path=ENV_PATH)

WORKSPACE = os.getenv("WORKSPACE", os.getcwd())
AREA_PRIVADA_URL = os.getenv("AREA_PRIVADA_URL", "https://ovt.gencat.cat/carpetaciutadana360#/acces")
DEFAULT_WAIT = int(os.getenv("DEFAULT_WAIT", "15"))
ALERT_ID = os.getenv("ALERT_ID", datetime.now().strftime("%Y%m%d_%H%M%S"))
ALERT_NAME = os.getenv("ALERT_NAME", "Area Privada")

# =========================
# Carpetas de ejecución
# =========================
run_dir = os.path.join(WORKSPACE, "runs", ALERT_ID)
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
  log("info", f"Captura guardada en: {filename}")
  return filename

def write_status(status_value):
  log("info", f"Escribiendo status: {status_value}")
  with open(os.path.join(logs_dir, "status.txt"), "w") as f:
      f.write(status_value)
  with open(os.path.join(WORKSPACE, "status.txt"), "w") as f:
      f.write(status_value)

# =========================
# Driver Selenium
# =========================
def setup_driver() -> webdriver.Firefox:
  profile_path = os.path.join(WORKSPACE, "profiles", "selenium_cert")
  if not os.path.exists(profile_path):
      log("error", f"Perfil Selenium no encontrado en: {profile_path}")
      sys.exit(2)

  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-gpu")
  options.add_argument("--window-size=1920,1080")
  options.profile = webdriver.FirefoxProfile(profile_path)

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
      log("info", f"Accediendo a: {AREA_PRIVADA_URL}")
      driver.get(AREA_PRIVADA_URL)
      WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")

      log("info", "Esperando botón principal en Área Privada...")
      try:
          elem = WebDriverWait(driver, DEFAULT_WAIT).until(
              EC.element_to_be_clickable((By.XPATH, "/main/app-acces/div/div[1]/button"))
          )
          log("info", "Botón encontrado y clicable → FALSO POSITIVO")
          save_screenshot(driver, "falso_positivo_area_privada")
          write_status("falso_positivo")
          return True
      except Exception as e:
          log("error", f"No se encontró el botón esperado: {e}")
          save_screenshot(driver, "error_area_privada")
          write_status("alarma_confirmada")
          return False

  except Exception as e:
      log("error", f"Error técnico crítico: {e}")
      save_screenshot(driver, "error_tecnico_area_privada")
      write_status("alarma_confirmada")
      return False
  finally:
      driver.quit()

if __name__ == "__main__":
  success = run_automation()
  sys.exit(0 if success else 1)
