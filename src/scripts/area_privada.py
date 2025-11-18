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
# Espera de loaders
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

# =========================
# Clic con soporte Shadow DOM
# =========================
def click_with_wait(driver, by, selector, description, iframe=False, shadow=False, shadow_script=None):
  try:
      wait_for_loaders(driver, timeout=20)
      if shadow and shadow_script:
          WebDriverWait(driver, DEFAULT_WAIT).until(lambda d: d.execute_script(shadow_script))
          elem = driver.execute_script(shadow_script)
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
      save_screenshot(driver, f"error_{description.replace(' ', '_')}")
      write_status("alarma_confirmada")
      return False

# =========================
# Flujo principal
# =========================
def run_automation():
  driver = setup_driver()
  try:
      log("info", f"Accediendo a: {AREA_PRIVADA_URL}")
      driver.get(AREA_PRIVADA_URL)
      WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")

      shadow_script = '''
          return document
              .querySelector("#single-spa-application\\\\:mfe-main-app > app-root")
              .shadowRoot
              .querySelector("main > app-acces > div > div.left > a");
      '''

      if click_with_wait(driver, None, None, "Botón principal Area Privada", shadow=True, shadow_script=shadow_script):
          save_screenshot(driver, "falso_positivo_area_privada")
          write_status("falso_positivo")
          return True
      else:
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
