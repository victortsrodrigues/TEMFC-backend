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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from urllib.parse import quote_plus
from config.settings import settings
from errors.csv_scraping_error import CSVScrapingError
from utils.sse_manager import sse_manager


class CSVScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.options = webdriver.ChromeOptions()
        for option in settings.CHROME_OPTIONS:
            self.options.add_argument(option)

    def get_csv_data(self, body, request_id=None):
        """Retrieve CSV data from CNES based on CPF or name"""
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=self.options)
        
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
                
                if not self._search_by_name(driver, name, request_id):
                    self.logger.warning(f"Could not find professional - CPF: {cpf}, name: {name}")
                    raise CSVScrapingError(
                        "Profissional não encontrado no CNES",
                        {"cpf": cpf, "name": name}
                    )
            return self._intercept_data(driver)
        
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            self.logger.error(f"Error during CSV scraping for CPF {cpf}: {e}")
            raise CSVScrapingError(
                "Erro durante a busca de dados",
                {"cpf": cpf, "name": name, "details": str(e)}
            )
        except CSVScrapingError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during CSV scraping for CPF {body.get('cpf')}: {e}")
            raise CSVScrapingError(
                "Erro inesperado ao buscar dados", 
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

    def _search_by_name(self, driver, name, request_id=None):
        try:
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    "Histórico não encontro pelo CPF. Tentando busca pelo nome", 
                    65, 
                    "in_progress"
                )
            
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
                        "Múltiplos profissionais encontrados para o nome fornecido",
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
                    "Funcionalidade de exportar o histórico não encontrada",
                    {"element": "CSV export button"}
                )
            
            self._click_element(driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", By.CSS_SELECTOR)
            intercepted_data = self._wait_for_intercepted_data(driver)
            if not intercepted_data:
                raise CSVScrapingError(
                    "Erro ao interceptar dados CSV",
                    {"reason": "Data interception timeout"}
                )
            
            return intercepted_data
        
        except NoSuchElementException as e:
            self.logger.warning(f"Element not found during CSV interception: {e}")
            raise CSVScrapingError(
                "Elemento não encontrado durante a exportação do CSV",
                {"details": str(e)}
            )
        except TimeoutException as e:
            self.logger.warning(f"Timeout during CSV interception: {e}")
            raise CSVScrapingError(
                "Operação demorando mais do que o esperado",
                {"details": str(e)}
            )
        except CSVScrapingError:
            raise
        except Exception as e:
            self.logger.warning(f"CSV data interception failed: {e}")
            raise CSVScrapingError(
                "Processo de exportação do CSV falhou",
                {"details": str(e)}
            )
    
    def _wait_for_element(self, driver, selector, by, timeout=20):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector)))
            return True
        except TimeoutException as e:
            self.logger.debug(f"Timeout waiting for element {selector}: {e}")
            raise TimeoutException(f"Timeout esperando pelo elemento: {selector}")
        except Exception as e:
            self.logger.debug(f"Error waiting for element {selector}: {e}")
            raise

    def _click_element(self, driver, selector, by=By.CSS_SELECTOR):
        try:
            element = WebDriverWait(driver, 20).until(
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
                            "Erro ao processar dados interceptados",
                            {"details": str(e)}
                        )
            time.sleep(1)
        return None
    
    def _json_to_csv(self, json_str):
        try:
            data = json.loads(json_str)
            if not data:
                raise CSVScrapingError(
                    "Recebido JSON vazio ou nulo",
                    {"reason": "Data is empty or null"}
                )
            
            # Extract top-level fields
            nome = data.get("nome")
            sexo = data.get("sexo")
            cns = data.get("cns")
            
            if not nome or not data.get("vinculos"):
                raise CSVScrapingError(
                    "Histórico profissional incompleto",	
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
                "Erro ao converter JSON para CSV",
                {"details": str(e)}
            )
        except CSVScrapingError:
            # Re-raise already formatted error
            raise
        except Exception as e:
            self.logger.error(f"Error converting JSON to CSV: {e}")
            raise CSVScrapingError(
                "Erro ao converter JSON para CSV",
                {"details": str(e)}
            )