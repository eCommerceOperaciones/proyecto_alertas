from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(
    service=Service("/usr/bin/geckodriver"), 
    options=options
)

driver.get("https://www.google.com")
print(driver.title)
driver.quit()
