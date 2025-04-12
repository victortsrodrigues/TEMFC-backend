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
    """
    Scraper for validating CNES establishments using the CNES Datasus website.
    """
    
    TIMEOUT_DEFAULT = 20

    def __init__(self):
        """
        Initialize the scraper with Chrome WebDriver options.
        """
        self.logger = logging.getLogger(__name__)
        self.options = webdriver.ChromeOptions()
        for option in settings.CHROME_OPTIONS:
            self.options.add_argument(option)

    def validate_online(self, cnes, establishment_name):
        """
        Validate an establishment online by CNES or name.

        Args:
            cnes: CNES code of the establishment.
            establishment_name: Name of the establishment.

        Returns:
            bool: True if the establishment is valid, False otherwise.

        Raises:
            ScrapingError: If an error occurs during validation.
        """
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
                "Operação demorou mais do que o esperado",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except NoSuchElementException as e:
            self.logger.error(f"Element not found for CNES {cnes}: {e}")
            raise ScrapingError(
                "Elemento não encontrado durante a validação",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for CNES {cnes}: {e}")
            raise ScrapingError(
                "Erro de WebDriver durante a validação",
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        except ScrapingError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during web scraping for CNES {cnes}: {e}")
            raise ScrapingError(
                "Erro inesperado durante a validação", 
                {"cnes": cnes, "name": establishment_name, "details": str(e)}
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error closing WebDriver: {e}")


    def _search_by_cnes(self, driver, cnes):
        """
        Search for an establishment by CNES code.

        Args:
            driver: Selenium WebDriver instance.
            cnes: CNES code of the establishment.

        Returns:
            bool: True if the establishment is found, False otherwise.
        """
        try:
            driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={cnes}")
            return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)
        except Exception as e:
            self.logger.error(f"Erro ao buscar pelo CPF: {e}")
            return False


    def _search_by_name(self, driver, name):
        """
        Search for an establishment by name.

        Args:
            driver: Selenium WebDriver instance.
            name: Name of the establishment.

        Returns:
            bool: True if the establishment is found, False otherwise.
        """
        try:
            encoded_name = name.replace(" ", "%20")
            driver.get(f"https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={encoded_name}")
            return self._wait_for_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", By.CSS_SELECTOR)
        except Exception as e:
            self.logger.error(f"Erro ao buscar pelo nome: {e}")
            return False


    def _check_services(self, driver):
        """
        Check if the establishment provides specific services.

        Args:
            driver: Selenium WebDriver instance.

        Returns:
            bool: True if the required services are found, False otherwise.
        """
        try:
            self._click_element(driver, "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span")
            if not self._wait_for_element(driver, "Conjunto", By.LINK_TEXT):
                self.logger.warning("Failed to find 'Conjunto' link")
                raise ScrapingError(
                    "Link 'Conjunto' não encontrado na página do estabelecimento",
                    {"details": "Element not found: 'Conjunto' link"}
                )
            
            self._click_element(driver, "Conjunto", By.LINK_TEXT)
            if not self._wait_for_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)", By.CSS_SELECTOR):
                self.logger.warning("Failed to find 'Serviços' link")
                raise ScrapingError(
                    "Link 'Serviços' não encontrado na página do estabelecimento",
                    {"details": "Element not found: 'Serviços' link"}
                )
            
            self._click_element(driver, "#estabContent > aside > section > ul > li.treeview.active > ul > li:nth-child(1)")
            if not self._wait_for_element(driver, "//table[@ng-table='tableParamsServicosEspecializados']", By.XPATH):
                self.logger.warning("Failed to find 'Serviços' table")
                raise ScrapingError(
                    "Tabela de serviços não encontrada na página do estabelecimento",
                    {"details": "Element not found: 'Serviços' table"}
                )
            
            rows = driver.find_elements(By.XPATH, "//table[@ng-table='tableParamsServicosEspecializados']//tbody//tr")
            for row in rows:
                code = row.find_element(By.XPATH, ".//td[@data-title-text='Código']").text
                if code in ["159", "152"]:
                    return True
            return False
        
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found during service check: {e}")
            raise ScrapingError(
                "Elemento não encontrado durante verificação de serviços",
                {"details": str(e)}
            )
        except Exception as e:
            self.logger.warning(f"Service check failed: {e}")
            raise ScrapingError(
                f"{str(e)}",
                {"details": str(e)}
            )
    
    
    def _wait_for_element(self, driver, selector, by):
        """
        Wait for an element to be present on the page.

        Args:
            driver: Selenium WebDriver instance.
            selector: Selector for the element.
            by: Type of selector (e.g., By.CSS_SELECTOR).
            timeout: Maximum wait time in seconds.

        Returns:
            bool: True if the element is found, False otherwise.
        """
        try:
            WebDriverWait(driver, self.TIMEOUT_DEFAULT).until(
                EC.presence_of_element_located((by, selector)))
            return True
        except TimeoutException as e:
            self.logger.debug(f"Timeout waiting for element {selector}: {e}")
            raise TimeoutException(f"Timeout esperando pelo elemento: {selector}")
        except Exception as e:
            self.logger.debug(f"Error waiting for element {selector}: {e}")
            raise


    def _click_element(self, driver, selector, by=By.CSS_SELECTOR):
        """
        Click an element on the page.

        Args:
            driver: Selenium WebDriver instance.
            selector: Selector for the element.
            by: Type of selector (e.g., By.CSS_SELECTOR).

        Raises:
            NoSuchElementException: If the element is not found.
            TimeoutException: If the element is not clickable.
        """
        try:    
            element = WebDriverWait(driver, self.TIMEOUT_DEFAULT).until(
            EC.element_to_be_clickable((by, selector)))
            element.click()
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found for clicking: {selector}")
            raise NoSuchElementException(f"Elemento não encontrado: {selector}")
        except TimeoutException as e:
            self.logger.warning(f"Timeout waiting for element to be clickable: {selector}")
            raise TimeoutException(f"Elemento não clicável: {selector}")
        except Exception as e:
            self.logger.warning(f"Failed to click element {selector}: {e}")
            raise