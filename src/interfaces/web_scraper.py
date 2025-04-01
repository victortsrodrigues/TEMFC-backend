from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
from config.settings import settings
import logging

class CNESScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.options = webdriver.ChromeOptions()
        for option in settings.CHROME_OPTIONS:
            self.options.add_argument(option)

    def validate_online(self, cnes, establishment_name):
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=self.options)
        try:
            if not self._search_by_cnes(driver, cnes):
                return self._search_by_name(driver, establishment_name)
            return self._check_services(driver)
        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
            return False
        finally:
            driver.quit()

    def _search_by_cnes(self, driver, cnes):
        driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={cnes}")
        return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)

    def _search_by_name(self, driver, name):
        encoded_name = quote_plus(name)
        driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={encoded_name}")
        return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)

    def _check_services(self, driver):
        try:
            self._click_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span")
            self._wait_for_element(driver, "Conjunto", By.LINK_TEXT, 5)
            self._click_element(driver, "Conjunto", By.LINK_TEXT)
            self._wait_for_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)", By.CSS_SELECTOR, 5)
            self._click_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)")
            self._wait_for_element(driver, "//table[@ng-table='tableParamsServicosEspecializados']", By.XPATH, 5)
            
            rows = driver.find_elements(By.XPATH, "//table[@ng-table='tableParamsServicosEspecializados']//tbody//tr")
            for row in rows:
                code = row.find_element(By.XPATH, ".//td[@data-title-text='Código']").text
                if code in ["159", "152"]:
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Service check failed: {e}")
            return False
    def _wait_for_element(self, driver, selector, by, timeout=5):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector)))
            return True
        except:
            return False

    def _click_element(self, driver, selector, by=By.CSS_SELECTOR):
        element = driver.find_element(by, selector)
        element.click()