import pytest
import json
from unittest.mock import MagicMock, patch, ANY
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from errors.csv_scraping_error import CSVScrapingError
from interfaces.csv_scraper import CSVScraper


class MockResponse:
    def __init__(self, body):
        self.body = body.encode('utf-8')


class MockRequest:
    def __init__(self, url, response=None):
        self.url = url
        self.response = response


@pytest.fixture
def mock_driver():
    # Create a mock driver with all the necessary methods and properties
    driver = MagicMock()
    driver.requests = []
    return driver


@pytest.fixture
def csv_scraper():
    with patch('src.interfaces.csv_scraper.webdriver.Chrome'), \
         patch('src.interfaces.csv_scraper.ChromeDriverManager'):
        scraper = CSVScraper()
        # Reduce timeout for faster tests
        scraper.TIMEOUT_DEFAULT = 1
        return scraper


@pytest.fixture
def sample_json_data():
    return json.dumps({
        "nome": "TEST USER",
        "sexo": "MASCULINO",
        "cns": "123456789012345",
        "vinculos": [
            {
                "nuComp": "202201",
                "coMun": "123456",
                "sigla": "UF",
                "noMun": "TEST CITY",
                "cbo": "123456",
                "dsCbo": "TEST PROFESSION",
                "cnes": "1234567",
                "cnpj": "12345678901234",
                "noFant": "TEST HOSPITAL",
                "natJur": "1000",
                "dsNatJur": "PUBLIC",
                "tpGestao": "MUNICIPAL",
                "tpSusNaoSus": "SUS",
                "vinculacao": "VINC_TEST",
                "vinculo": "EMP_TEST",
                "subVinculo": "SUBVINC_TEST",
                "chOutros": "10",
                "chAmb": "20",
                "chHosp": "30"
            }
        ]
    })


class TestCSVScraper:
    
    @patch('src.interfaces.csv_scraper.webdriver.Chrome')
    @patch('src.interfaces.csv_scraper.Service')
    @patch('src.interfaces.csv_scraper.ChromeDriverManager')
    def test_get_csv_data_with_cpf_success(self, mock_manager, mock_service, mock_chrome, csv_scraper, mock_driver):
        """Test successful CSV data retrieval using CPF"""
        # Setup
        mock_chrome.return_value = mock_driver
        csv_scraper._search_by_cpf = MagicMock(return_value=True)
        csv_scraper._intercept_data = MagicMock(return_value="CSV DATA")
        
        # Execute
        result = csv_scraper.get_csv_data({"cpf": "123.456.789-10"})
        
        # Assert
        assert result == "CSV DATA"
        csv_scraper._search_by_cpf.assert_called_once_with(mock_driver, "12345678910")
        csv_scraper._intercept_data.assert_called_once_with(mock_driver)
        mock_driver.quit.assert_called_once()
    
    @patch('src.interfaces.csv_scraper.webdriver.Chrome')
    @patch('src.interfaces.csv_scraper.Service')
    @patch('src.interfaces.csv_scraper.ChromeDriverManager')
    def test_get_csv_data_fallback_to_name(self, mock_manager, mock_service, mock_chrome, csv_scraper, mock_driver):
        """Test CSV data retrieval falling back to name search when CPF search fails"""
        # Setup
        mock_chrome.return_value = mock_driver
        csv_scraper._search_by_cpf = MagicMock(return_value=False)
        csv_scraper._search_by_name = MagicMock(return_value=True)
        csv_scraper._intercept_data = MagicMock(return_value="CSV DATA")
        
        # Execute
        result = csv_scraper.get_csv_data({"cpf": "123.456.789-10", "name": "John Doe"})
        
        # Assert
        assert result == "CSV DATA"
        csv_scraper._search_by_cpf.assert_called_once_with(mock_driver, "12345678910")
        csv_scraper._search_by_name.assert_called_once_with(mock_driver, "JOHN DOE", None)
        csv_scraper._intercept_data.assert_called_once_with(mock_driver)
    
    @patch('src.interfaces.csv_scraper.webdriver.Chrome')
    @patch('src.interfaces.csv_scraper.Service')
    @patch('src.interfaces.csv_scraper.ChromeDriverManager')
    def test_get_csv_data_not_found(self, mock_manager, mock_service, mock_chrome, csv_scraper, mock_driver):
        """Test error handling when professional is not found"""
        # Setup
        mock_chrome.return_value = mock_driver
        csv_scraper._search_by_cpf = MagicMock(return_value=False)
        csv_scraper._search_by_name = MagicMock(return_value=False)
        
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper.get_csv_data({"cpf": "123.456.789-10", "name": "John Doe"})
        
        # Check exception details
        assert "Profissional não encontrado no CNES" in str(excinfo.value)
        mock_driver.quit.assert_called_once()
    
    @patch('src.interfaces.csv_scraper.webdriver.Chrome')
    @patch('src.interfaces.csv_scraper.Service')
    @patch('src.interfaces.csv_scraper.ChromeDriverManager')
    def test_get_csv_data_with_selenium_exception(self, mock_manager, mock_service, mock_chrome, csv_scraper, mock_driver):
        """Test error handling when Selenium raises an exception"""
        # Setup
        mock_chrome.return_value = mock_driver
        csv_scraper._search_by_cpf = MagicMock(side_effect=TimeoutException("Timeout"))
        
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper.get_csv_data({"cpf": "123.456.789-10"})
        
        # Check exception details
        assert "Erro durante a busca de dados" in str(excinfo.value)
        mock_driver.quit.assert_called_once()
    
    @patch('src.interfaces.csv_scraper.webdriver.Chrome')
    @patch('src.interfaces.csv_scraper.Service')
    @patch('src.interfaces.csv_scraper.ChromeDriverManager')
    def test_driver_quit_exception_handling(self, mock_manager, mock_service, mock_chrome, csv_scraper, mock_driver):
        """Test handling of exceptions when quitting the driver"""
        # Setup
        mock_chrome.return_value = mock_driver
        mock_driver.quit.side_effect = Exception("Driver quit error")
        csv_scraper._search_by_cpf = MagicMock(side_effect=Exception("Test error"))
        
        # Execute and Assert - should not raise exception from driver.quit()
        with pytest.raises(CSVScrapingError):
            csv_scraper.get_csv_data({"cpf": "123.456.789-10"})
        
        # Verify quit was called even though it raised an exception
        mock_driver.quit.assert_called_once()
    
    def test_search_by_cpf_success(self, csv_scraper, mock_driver):
        """Test successful search by CPF"""
        # Setup
        csv_scraper._wait_for_element = MagicMock(return_value=True)
        
        # Execute
        result = csv_scraper._search_by_cpf(mock_driver, "12345678910")
        
        # Assert
        assert result is True
        mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search=12345678910")
        csv_scraper._wait_for_element.assert_called_once_with(
            mock_driver, 
            "button.btn.btn-default[ng-click*='historicoProfissional']", 
            ANY
        )
    
    def test_search_by_cpf_failure(self, csv_scraper, mock_driver):
        """Test CPF search that fails"""
        # Setup
        csv_scraper._wait_for_element = MagicMock(side_effect=Exception("Element not found"))
        
        # Execute
        result = csv_scraper._search_by_cpf(mock_driver, "12345678910")
        
        # Assert
        assert result is False
    
    def test_search_by_name_success(self, csv_scraper, mock_driver):
        """Test successful search by name"""
        # Setup
        csv_scraper._wait_for_element = MagicMock(return_value=True)
        mock_driver.find_elements.return_value = [MagicMock()]  # Single button found
        
        # Execute
        result = csv_scraper._search_by_name(mock_driver, "JOHN DOE")
        
        # Assert
        assert result is True
        mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search=JOHN%20DOE")
    
    def test_search_by_name_multiple_results(self, csv_scraper, mock_driver):
        """Test name search returning multiple results (should raise an error)"""
        # Setup
        csv_scraper._wait_for_element = MagicMock(return_value=True)
        mock_driver.find_elements.return_value = [MagicMock(), MagicMock()]  # Multiple buttons found
        csv_scraper.MAX_QUANT_BUTTONS = 1
        
         # Execute
        result = csv_scraper._search_by_name(mock_driver, "JOHN DOE")
        
        # Assert
        assert result is False
        
    def test_intercept_data_success(self, csv_scraper, mock_driver):
        """Test successful data interception"""
        # Setup
        csv_scraper._click_element = MagicMock()
        csv_scraper._wait_for_element = MagicMock(return_value=True)
        csv_scraper._wait_for_intercepted_data = MagicMock(return_value="CSV DATA")
        
        # Execute
        result = csv_scraper._intercept_data(mock_driver)
        
        # Assert
        assert result == "CSV DATA"
        csv_scraper._click_element.assert_any_call(mock_driver, "button.btn.btn-default[ng-click*='historicoProfissional']")
        csv_scraper._click_element.assert_any_call(mock_driver, "button.btn.btn-primary[ng-csv='getHistoricoProfissional()']", ANY)
    
    def test_intercept_data_no_export_button(self, csv_scraper, mock_driver):
        """Test case when export button is not found"""
        # Setup
        csv_scraper._click_element = MagicMock()
        csv_scraper._wait_for_element = MagicMock(return_value=False)
        
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper._intercept_data(mock_driver)
        
        # Check exception details
        assert "Funcionalidade de exportar o histórico não encontrada" in str(excinfo.value)
    
    def test_intercept_data_no_data_intercepted(self, csv_scraper, mock_driver):
        """Test case when no data is intercepted"""
        # Setup
        csv_scraper._click_element = MagicMock()
        csv_scraper._wait_for_element = MagicMock(return_value=True)
        csv_scraper._wait_for_intercepted_data = MagicMock(return_value=None)
        
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper._intercept_data(mock_driver)
        
        # Check exception details
        assert "Erro ao interceptar dados CSV" in str(excinfo.value)
    
    def test_wait_for_element_success(self, csv_scraper, mock_driver):
        """Test successful wait for element"""
        # Setup
        with patch('src.interfaces.csv_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = True
            
            # Execute
            result = csv_scraper._wait_for_element(mock_driver, "test-selector", ANY)
            
            # Assert
            assert result is True
    
    def test_wait_for_element_timeout(self, csv_scraper, mock_driver):
        """Test timeout while waiting for element"""
        # Setup
        with patch('interfaces.csv_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("Timeout")
            
            # Execute and Assert
            with pytest.raises(TimeoutException) as excinfo:
                csv_scraper._wait_for_element(mock_driver, "test-selector", ANY)
            
            # Check exception details
            assert "Timeout esperando pelo elemento" in str(excinfo.value)
    
    def test_click_element_success(self, csv_scraper, mock_driver):
        """Test successful element click"""
        # Setup
        mock_element = MagicMock()
        with patch('interfaces.csv_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = mock_element
            
            # Execute
            csv_scraper._click_element(mock_driver, "test-selector")
            
            # Assert
            mock_element.click.assert_called_once()
    
    def test_click_element_not_found(self, csv_scraper, mock_driver):
        """Test error when element to click is not found"""
        # Setup
        with patch('interfaces.csv_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = NoSuchElementException("Element not found")
            
            # Execute and Assert
            with pytest.raises(NoSuchElementException) as excinfo:
                csv_scraper._click_element(mock_driver, "test-selector")
            
            # Check exception details
            assert "Elemento não encontrado" in str(excinfo.value)
    
    def test_wait_for_intercepted_data_success(self, csv_scraper, mock_driver, sample_json_data):
        """Test successful interception of data"""
        # Setup
        mock_request = MockRequest(
            url="https://cnes.datasus.gov.br/api/historico-profissional",
            response=MockResponse(sample_json_data)
        )
        mock_driver.requests = [mock_request]
        
        with patch.object(csv_scraper, '_json_to_csv', return_value="CSV DATA"):
            # Execute
            result = csv_scraper._wait_for_intercepted_data(mock_driver)
            
            # Assert
            assert result == "CSV DATA"
            csv_scraper._json_to_csv.assert_called_once_with(sample_json_data)
    
    def test_wait_for_intercepted_data_timeout(self, csv_scraper, mock_driver):
        """Test timeout while waiting for intercepted data"""
        # Setup - empty requests
        mock_driver.requests = []
        
        # Override TIMEOUT_DEFAULT to speed up test
        csv_scraper.TIMEOUT_DEFAULT = 0.1
        
        # Execute
        result = csv_scraper._wait_for_intercepted_data(mock_driver)
        
        # Assert
        assert result is None
    
    def test_json_to_csv_conversion(self, csv_scraper, sample_json_data):
        """Test correct JSON to CSV conversion"""
        # Execute
        result = csv_scraper._json_to_csv(sample_json_data)
        
        # Assert
        assert "NOME;SEXO;CNS;COMP.;IBGE;UF;MUNICIPIO;CBO;DESCRICAO CBO;" in result
        assert "TEST USER;MASCULINO;123456789012345;202201;" in result
        assert "TEST CITY;123456;TEST PROFESSION;1234567;12345678901234;" in result
    
    def test_json_to_csv_empty_data(self, csv_scraper):
        """Test JSON to CSV conversion with empty data"""
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper._json_to_csv("{}")
        
        # Check exception details
        assert "Recebido JSON vazio ou nulo" in str(excinfo.value)
    
    def test_json_to_csv_invalid_json(self, csv_scraper):
        """Test JSON to CSV conversion with invalid JSON"""
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper._json_to_csv("{invalid json")
        
        # Check exception details
        assert "Erro ao converter JSON para CSV" in str(excinfo.value)
    
    def test_json_to_csv_missing_vinculos(self, csv_scraper):
        """Test JSON to CSV conversion with missing vinculos"""
        # Setup
        invalid_json = json.dumps({"nome": "TEST USER", "sexo": "MASCULINO", "cns": "123456789012345"})
        
        # Execute and Assert
        with pytest.raises(CSVScrapingError) as excinfo:
            csv_scraper._json_to_csv(invalid_json)
        
        # Check exception details
        assert "Histórico profissional incompleto" in str(excinfo.value)