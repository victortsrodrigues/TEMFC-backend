from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from urllib.parse import quote_plus
from config.settings import settings
from errors.establishment_scraping_error import ScrapingError
import logging

class CNESScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.options = webdriver.ChromeOptions()
        for option in settings.CHROME_OPTIONS:
            self.options.add_argument(option)

    def validate_online(self, cnes, establishment_name):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=self.options)
        try:
            if not self._search_by_cnes(driver, cnes):
                self.logger.info(f"CNES search failed for {cnes}, trying name search")
                
                if not self._search_by_name(driver, establishment_name):
                    self.logger.warning(f"Could not find establishment - CNES: {cnes}, name: {establishment_name}")
                    return False
            
            return self._check_services(driver)
        
        except TimeoutException as e:
            self.logger.error(f"Timeout during web scraping for CNES {cnes}: {e}")
            raise ScrapingError(
                "Operation timed out during validation",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except NoSuchElementException as e:
            self.logger.error(f"Element not found for CNES {cnes}: {e}")
            raise ScrapingError(
                "Required element not found during validation",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for CNES {cnes}: {e}")
            raise ScrapingError(
                "WebDriver error during validation",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except ScrapingError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during web scraping for CNES {cnes}: {e}")
            raise ScrapingError(
                "Web validation failed", 
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error closing WebDriver: {e}")


    def _search_by_cnes(self, driver, cnes):
        try:
            driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={cnes}")
            return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)
        except Exception as e:
            self.logger.error(f"Error searching by CNES: {e}")
            return False


    def _search_by_name(self, driver, name):
        try:
            encoded_name = quote_plus(name)
            driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={encoded_name}")
            return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)
        except Exception as e:
            self.logger.error(f"Error searching by name: {e}")
            return False


    def _check_services(self, driver):
        try:
            self._click_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span")
            if not self._wait_for_element(driver, "Conjunto", By.LINK_TEXT, 5):
                self.logger.warning("Failed to find 'Conjunto' link")
                return False
            
            self._click_element(driver, "Conjunto", By.LINK_TEXT)
            if not self._wait_for_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)", By.CSS_SELECTOR, 5):
                self.logger.warning("Failed to find 'Serviços' link")
                return False
            
            self._click_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)")
            if not self._wait_for_element(driver, "//table[@ng-table='tableParamsServicosEspecializados']", By.XPATH, 5):
                self.logger.warning("Failed to find 'Serviços' table")
                return False
            
            rows = driver.find_elements(By.XPATH, "//table[@ng-table='tableParamsServicosEspecializados']//tbody//tr")
            for row in rows:
                code = row.find_element(By.XPATH, ".//td[@data-title-text='Código']").text
                if code in ["159", "152"]:
                    return True
            return False
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found during service check: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Service check failed: {e}")
            return False
    
    
    def _wait_for_element(self, driver, selector, by, timeout=30):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector)))
            return True
        except TimeoutException as e:
            self.logger.debug(f"Timeout waiting for element {selector}: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"Error waiting for element {selector}: {e}")
            return False


    def _click_element(self, driver, selector, by=By.CSS_SELECTOR):
        try:    
            element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((by, selector)))
            element.click()
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found for clicking: {selector}")
            raise NoSuchElementException(f"Element not found: {selector}")
        except TimeoutException as e:
            self.logger.warning(f"Timeout waiting for element to be clickable: {selector}")
            raise TimeoutException(f"Element not clickable: {selector}")
        except Exception as e:
            self.logger.warning(f"Failed to click element {selector}: {e}")
            raise