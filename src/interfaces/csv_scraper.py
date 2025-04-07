import csv
import json
import logging
import time
from io import StringIO
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from urllib.parse import quote_plus
from config.settings import settings
from errors.csv_scraping_error import CSVScrapingError


class CSVScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.options = webdriver.ChromeOptions()
        for option in settings.CHROME_OPTIONS:
            self.options.add_argument(option)

    def get_csv_data(self, body):
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=self.options)
        
        cpf = body.get("cpf")
        if cpf:
            cpf = cpf.replace(".", "").replace("-", "").replace(" ", "").strip().zfill(11)
            body["cpf"] = cpf
        name = body.get("name")
        if name:
            name = name.strip().upper()
            body["name"] = name
        
        try:
            if not self._search_by_cpf(driver, cpf):
                self.logger.info(f"CPF search failed for {cpf}, trying name search")
                
                if not self._search_by_name(driver, name):
                    self.logger.warning(f"Could not find professional - CPF: {cpf}, name: {name}")
                    raise CSVScrapingError(
                        "Professional not found in CNES database",
                        {"cpf": cpf, "name": name}
                    )
            return self._intercept_data(driver)
        
        except TimeoutException as e:
            self.logger.error(f"Timeout during CSV scraping for CPF {body.get('cpf')}: {e}")
            raise CSVScrapingError(
                "Operation timed out during data retrieval",
                {"cpf": body.get("cpf"), "name": body.get("name"), "details": str(e)}
            )
        except NoSuchElementException as e:
            self.logger.error(f"Element not found for CPF {body.get('cpf')}: {e}")
            raise CSVScrapingError(
                "Required element not found during data retrieval",
                {"cpf": body.get("cpf"), "name": body.get("name"), "details": str(e)}
            )
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for CPF {body.get('cpf')}: {e}")
            raise CSVScrapingError(
                "WebDriver error during data retrieval",
                {"cpf": body.get("cpf"), "name": body.get("name"), "details": str(e)}
            )
        except CSVScrapingError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during CSV scraping for CPF {body.get('cpf')}: {e}")
            raise CSVScrapingError(
                "CSV data retrieval failed", 
                {"cpf": body.get("cpf"), "name": body.get("name"), "details": str(e)}
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error closing WebDriver: {e}")

    def _search_by_cpf(self, driver, cpf):
        try:
            driver.get(f"https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search={cpf}")
            del driver.requests
            return self._wait_for_element(driver, "button.btn.btn-default[ng-click*='historicoProfissional']", By.CSS_SELECTOR)
        except Exception as e:
            self.logger.warning(f"Error searching by CPF {cpf}: {e}")
            return False

    def _search_by_name(self, driver, name):
        try:
            encoded_name = name.replace(" ", "%20")
            driver.get(f"https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search={encoded_name}")
            del driver.requests
            found = self._wait_for_element(driver, "button.btn.btn-default[ng-click*='historicoProfissional']", By.CSS_SELECTOR)
            if found:
                # Check the number of buttons
                buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn.btn-default[ng-click*='historicoProfissional']")
                if len(buttons) > 1:
                    self.logger.warning(f"Multiple professionals found for name: {name}")
                    raise CSVScrapingError(
                        "Multiple professionals found with the provided name",
                        {"name": name}
                    )
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Error searching by name {name}: {e}")
            return False

    def _intercept_data(self, driver):
        try:
            self._click_element(driver, "button.btn.btn-default[ng-click*='historicoProfissional']")
            if not self._wait_for_element(driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", By.CSS_SELECTOR, 5):
                self.logger.warning("CSV export button not found")
                raise CSVScrapingError(
                    "CSV export functionality not available",
                    {"element": "CSV export button"}
                )
            
            self._click_element(driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", By.CSS_SELECTOR)
            intercepted_data = self._wait_for_intercepted_data(driver)
            if not intercepted_data:
                raise CSVScrapingError(
                    "Failed to retrieve CSV data",
                    {"reason": "Data interception timeout"}
                )
            
            return intercepted_data
        
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found during CSV interception: {e}")
            raise CSVScrapingError(
                "Required element not found during data export",
                {"details": str(e)}
            )
        except TimeoutException as e:
            self.logger.warning(f"Timeout during CSV interception: {e}")
            raise CSVScrapingError(
                "Operation timed out during data export",
                {"details": str(e)}
            )
        except CSVScrapingError:
            raise
        except Exception as e:
            self.logger.warning(f"CSV data interception failed: {e}")
            raise CSVScrapingError(
                "CSV data export failed",
                {"details": str(e)}
            )
    
    def _wait_for_element(self, driver, selector, by, timeout=5):
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
            element = WebDriverWait(driver, 5).until(
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
        
    def _wait_for_intercepted_data(self, driver, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            for request in driver.requests:
                if request.response and "historico-profissional" in request.url:
                    try:
                        json_data = request.response.body.decode("utf-8")
                        csv_data = self._json_to_csv(json_data)  # Convert JSON to CSV
                        return csv_data
                    except Exception as e:
                        self.logger.error(f"Error processing intercepted data: {e}")
                        raise CSVScrapingError(
                            "Failed to process intercepted data",
                            {"details": str(e)}
                        )
            time.sleep(1)
        return None
    
    def _json_to_csv(self, json_str):
        try:
            data = json.loads(json_str)
            if not data:
                raise CSVScrapingError(
                    "Empty or invalid JSON data received",
                    {"reason": "Data is empty or null"}
                )
            
            # Extract top-level fields
            nome = data.get("nome")
            sexo = data.get("sexo")
            cns = data.get("cns")
            
            if not nome or not data.get("vinculos"):
                raise CSVScrapingError(
                    "Incomplete professional data received",
                    {"reason": "Missing name or employment history"}
                )
            
            # Define CSV headers in correct order
            headers = [
                "NOME", "SEXO", "CNS", "COMP.", "IBGE", "UF", "MUNICIPIO", "CBO",
                "DESCRICAO CBO", "CNES", "CNPJ", "ESTABELECIMENTO", "NATUREZA JURIDICA",
                "DESCRICAO NATUREZA JURIDICA", "GESTAO", "SUS", "VINCULO ESTABELECIMENTO",
                "VINCULO EMPREGADOR", "DETALHAMENTO DO VINCULO", "CHS OUTROS", "CHS AMB.",
                "CHS HOSP."
            ]
            
            # Build rows combining top-level and nested data
            items = []
            for vinculo in data.get("vinculos", []):
                row = {
                    # Top-level fields
                    "NOME": nome,
                    "SEXO": sexo,
                    "CNS": cns,
                    
                    # Nested fields with key mapping
                    "COMP.": vinculo.get("nuComp"),
                    "IBGE": vinculo.get("coMun"),
                    "UF": vinculo.get("sigla"),
                    "MUNICIPIO": vinculo.get("noMun"),
                    "CBO": vinculo.get("cbo"),
                    "DESCRICAO CBO": vinculo.get("dsCbo"),
                    "CNES": vinculo.get("cnes"),
                    "CNPJ": vinculo.get("cnpj"),
                    "ESTABELECIMENTO": vinculo.get("noFant"),
                    "NATUREZA JURIDICA": vinculo.get("natJur"),
                    "DESCRICAO NATUREZA JURIDICA": vinculo.get("dsNatJur"),
                    "GESTAO": vinculo.get("tpGestao"),
                    "SUS": vinculo.get("tpSusNaoSus"),
                    "VINCULO ESTABELECIMENTO": vinculo.get("vinculacao"),
                    "VINCULO EMPREGADOR": vinculo.get("vinculo"),
                    "DETALHAMENTO DO VINCULO": vinculo.get("subVinculo"),
                    "CHS OUTROS": vinculo.get("chOutros"),
                    "CHS AMB.": vinculo.get("chAmb"),
                    "CHS HOSP.": vinculo.get("chHosp")
                }
                items.append(row)
            
            # Create CSV in-memory
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
            writer.writeheader()
            writer.writerows(items)
            
            return output.getvalue()
        
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            raise CSVScrapingError(
                "Failed to parse JSON data",
                {"details": str(e)}
            )
        except CSVScrapingError:
            # Re-raise already formatted error
            raise
        except Exception as e:
            self.logger.error(f"Error converting JSON to CSV: {e}")
            raise CSVScrapingError(
                "Failed to convert JSON to CSV format",
                {"details": str(e)}
            )