from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
from config.settings import settings
import csv
from io import StringIO
import json
import logging
import time

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
            name = name.strip()
            body["name"] = name
        
        try:
            if not self._search_by_cpf(driver, cpf):
                return self._search_by_name(driver, name)
            return self._intercept_data(driver)
        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
            return None
        finally:
            driver.quit()

    def _search_by_cpf(self, driver, cpf):
        driver.get(f"https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search={cpf}")
        del driver.requests
        return self._wait_for_element(driver, 'table[ng-table="tableParams"]', By.CSS_SELECTOR)

    def _search_by_name(self, driver, name):
        encoded_name = quote_plus(name)
        driver.get(f"https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search={encoded_name}")
        del driver.requests
        return self._wait_for_element(driver, 'table[ng-table="tableParams"]', By.CSS_SELECTOR)

    def _intercept_data(self, driver):
        try:
            self._click_element(driver, "button.btn.btn-default[ng-click*='historicoProfissional']")
            self._wait_for_element(driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", By.CSS_SELECTOR, 5)
            self._click_element(driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", By.CSS_SELECTOR)
            return self._wait_for_intercepted_data(driver)
        
        except Exception as e:
            self.logger.warning(f"Service check failed: {e}")
            return None
    
    def _wait_for_element(self, driver, selector, by, timeout=5):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector)))
            return True
        except:
            return False

    def _click_element(self, driver, selector, by=By.CSS_SELECTOR):
        element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((by, selector)))
        element.click()
        
    def _wait_for_intercepted_data(self, driver, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            for request in driver.requests:
                if request.response and "historico-profissional" in request.url:
                    json_data = request.response.body.decode("utf-8")
                    csv_data = self._json_to_csv(json_data)  # Convert JSON to CSV
                    return csv_data
            time.sleep(1)
        return None
    
    def _json_to_csv(self, json_str):
        data = json.loads(json_str)
        
        # Extract top-level fields
        nome = data.get("nome")
        sexo = data.get("sexo")
        cns = data.get("cns")
        
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