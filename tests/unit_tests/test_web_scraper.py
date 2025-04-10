import pytest
import json

from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

from interfaces.establishment_scraper import CNESScraper
from errors.establishment_scraping_error import ScrapingError

class TestCNESScraper:
    """Test suite for CNESScraper class"""

    def setup_method(self):
        self.scraper = CNESScraper()
        self.scraper.logger = Mock()
    
    @pytest.fixture
    def web_scraper(self):
        """Create a CNESScraper instance with mocked webdriver"""
        with patch('src.interfaces.web_scraper'):
            scraper = CNESScraper()
            yield scraper

    @pytest.fixture
    def mock_driver(self):
        """Create a mocked Chrome driver"""
        mock = MagicMock()
        mock.requests = []
        return mock

    @pytest.fixture
    def mock_successful_request(self):
        """Create a mock request with successful response"""
        mock_request = MagicMock()
        mock_request.url = "https://example.com/historico-profissional"
        
        # Sample JSON response from the CNES system
        sample_json = {
            "nome": "TEST PROFESSIONAL",
            "sexo": "M",
            "cns": "123456789012345",
            "vinculos": [
                {
                    "nuComp": "01/2023",
                    "coMun": "123456",
                    "sigla": "SP",
                    "noMun": "SAO PAULO",
                    "cbo": "225125",
                    "dsCbo": "MEDICO CLINICO",
                    "cnes": "1234567",
                    "cnpj": "12345678901234",
                    "noFant": "HOSPITAL TEST",
                    "natJur": "1000",
                    "dsNatJur": "ADMINISTRACAO PUBLICA",
                    "tpGestao": "M",
                    "tpSusNaoSus": "SUS",
                    "vinculacao": "VINCULO EMPREGATICIO",
                    "vinculo": "ESTATUTARIO",
                    "subVinculo": "REGIME JURIDICO UNICO",
                    "chOutros": "0",
                    "chAmb": "40",
                    "chHosp": "0"
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.body = json.dumps(sample_json).encode('utf-8')
        mock_request.response = mock_response
        
        return mock_request

    @pytest.fixture
    def mock_empty_json_request(self):
        """Create a mock request with empty JSON response"""
        mock_request = MagicMock()
        mock_request.url = "https://example.com/historico-profissional"
        
        mock_response = MagicMock()
        mock_response.body = json.dumps({}).encode('utf-8')
        mock_request.response = mock_response
        
        return mock_request

    @pytest.fixture
    def mock_invalid_json_request(self):
        """Create a mock request with invalid JSON response"""
        mock_request = MagicMock()
        mock_request.url = "https://example.com/historico-profissional"
        
        mock_response = MagicMock()
        mock_response.body = "Invalid JSON".encode('utf-8')
        mock_request.response = mock_response
        
        return mock_request

    def test_init(self, web_scraper):
        """Test CSVScraper initialization"""
        assert web_scraper.logger is not None
        assert web_scraper.options is not None
        

    def test_search_by_cnes_success(self, web_scraper, mock_driver):
        """Test successful search by CNES"""
        # Arrange
        with patch.object(web_scraper, '_wait_for_element', return_value=True) as mock_wait:
            # Act
            result = web_scraper._search_by_cnes(mock_driver, "1234567")
            
            # Assert
            assert result is True
            mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search=1234567")
            mock_wait.assert_called_once()

    def test_search_by_cpf_failure(self, web_scraper, mock_driver):
        """Test failed search by CNES"""
        # Arrange
        with patch.object(web_scraper, '_wait_for_element', return_value=False) as mock_wait:
            # Act
            result = web_scraper._search_by_cnes(mock_driver, "1234567")
            
            # Assert
            assert result is False
            mock_driver.get.assert_called_once()
            mock_wait.assert_called_once()

    def test_search_by_cpf_exception(self, web_scraper, mock_driver):
        """Test exception handling during search by CPF"""
        # Arrange
        mock_driver.get.side_effect = Exception("Error accessing URL")
        
        # Act
        result = web_scraper._search_by_cnes(mock_driver, "1234567")
        
        # Assert
        assert result is False
        mock_driver.get.assert_called_once()

    def test_search_by_name_success(self, web_scraper, mock_driver):
        """Test successful search by name"""
        # Arrange
        with patch.object(web_scraper, '_wait_for_element', return_value=True) as mock_wait:
            # Act
            result = web_scraper._search_by_name(mock_driver, "TEST NAME")
            
            # Assert
            assert result is True
            mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search=TEST+NAME")
            mock_wait.assert_called_once()

    def test_search_by_name_failure(self, web_scraper, mock_driver):
        """Test failed search by name"""
        # Arrange
        with patch.object(web_scraper, '_wait_for_element', return_value=False) as mock_wait:
            # Act
            result = web_scraper._search_by_name(mock_driver, "TEST NAME")
            
            # Assert
            assert result is False
            mock_driver.get.assert_called_once()
            mock_wait.assert_called_once()

    def test_search_by_name_exception(self, web_scraper, mock_driver):
        """Test exception handling during search by name"""
        # Arrange
        mock_driver.get.side_effect = Exception("Error accessing URL")
        
        # Act
        result = web_scraper._search_by_name(mock_driver, "TEST NAME")
        
        # Assert
        assert result is False
        mock_driver.get.assert_called_once()

    def test_wait_for_element_success(self, web_scraper, mock_driver):
        """Test successful element wait"""
        # Arrange
        mock_wait = MagicMock()
        with patch('src.interfaces.web_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = web_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is True
            mock_wait_class.assert_called_once_with(mock_driver, 5)

    def test_wait_for_element_timeout(self, web_scraper, mock_driver):
        """Test element wait timeout"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Timeout")
        with patch('src.interfaces.web_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = web_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is False
            mock_wait_class.assert_called_once()

    def test_wait_for_element_exception(self, web_scraper, mock_driver):
        """Test element wait general exception"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = Exception("General error")
        with patch('src.interfaces.web_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = web_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is False
            mock_wait_class.assert_called_once()

    def test_click_element_success(self, web_scraper, mock_driver):
        """Test successful element click"""
        # Arrange
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        # Act
        web_scraper._click_element(mock_driver, "test-selector")
        
        # Assert
        mock_element.click.assert_called_once()

    def test_click_element_not_found(self, web_scraper, mock_driver):
        """Test element click when element not found"""
        # Arrange
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
        # Act & Assert
        with pytest.raises(NoSuchElementException) as excinfo:
            web_scraper._click_element(mock_driver, "test-selector")

        assert "Element not found" in str(excinfo.value)

    def test_click_element_general_exception(self, web_scraper, mock_driver):
        """Test element click general exception"""
        # Arrange
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        mock_driver.find_element.side_effect = WebDriverException("WebDriver error")
        selector = "test-selector"
        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            web_scraper._click_element(mock_driver, selector)
       
        assert "WebDriver error" in str(excinfo.value)


    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_success_with_matching_code(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        mock_row1 = Mock()
        mock_row1.find_element.return_value.text = "159"
        mock_row2 = Mock()
        mock_row2.find_element.return_value.text = "123"
        mock_driver.find_elements.return_value = [mock_row1, mock_row2]
        
        # Configure mocks to simulate successful navigation
        mock_wait.return_value = True
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is True
        assert mock_click.call_count == 3
        assert mock_wait.call_count == 3
        mock_driver.find_elements.assert_called_once_with(
            By.XPATH, "//table[@ng-table='tableParamsServicosEspecializados']//tbody//tr"
        )
        mock_row1.find_element.assert_called_once_with(
            By.XPATH, ".//td[@data-title-text='Código']"
        )
  

    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_success_with_no_matching_code(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        mock_row1 = Mock()
        mock_row1.find_element.return_value.text = "123"
        mock_row2 = Mock()
        mock_row2.find_element.return_value.text = "456"
        mock_driver.find_elements.return_value = [mock_row1, mock_row2]
        
        # Configure mocks to simulate successful navigation
        mock_wait.return_value = True
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        assert mock_click.call_count == 3
        assert mock_wait.call_count == 3
        mock_driver.find_elements.assert_called_once()
    
    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_fail_at_conjunto_link(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        
        # Configure mocks to simulate failure at first navigation step
        mock_wait.side_effect = [False]  # Fail at first wait
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        mock_click.assert_called_once()
        mock_wait.assert_called_once()
        self.scraper.logger.warning.assert_called_once_with("Failed to find 'Conjunto' link")
    
    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_fail_at_servicos_link(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        
        # Configure mocks to simulate failure at second navigation step
        mock_wait.side_effect = [True, False]  # Succeed first, fail second
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        assert mock_click.call_count == 2
        assert mock_wait.call_count == 2
        self.scraper.logger.warning.assert_called_once_with("Failed to find 'Serviços' link")
    
    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_fail_at_servicos_table(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        
        # Configure mocks to simulate failure at third navigation step
        mock_wait.side_effect = [True, True, False]  # Succeed first two, fail third
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        assert mock_click.call_count == 3
        assert mock_wait.call_count == 3
        self.scraper.logger.warning.assert_called_once_with("Failed to find 'Serviços' table")
    
    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_element_not_found_exception(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        mock_wait.return_value = True
        mock_driver.find_elements.side_effect = NoSuchElementException("Element not found")
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        self.scraper.logger.warning.assert_called_once()
        assert "Element not found during service check" in self.scraper.logger.warning.call_args[0][0]
    
    @patch.object(CNESScraper, '_wait_for_element')
    @patch.object(CNESScraper, '_click_element')
    def test_check_services_general_exception(self, mock_click, mock_wait):
        # Arrange
        mock_driver = Mock()
        mock_wait.return_value = True
        mock_driver.find_elements.side_effect = Exception("General error")
        
        # Act
        result = self.scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        self.scraper.logger.warning.assert_called_once()
        assert "Service check failed" in self.scraper.logger.warning.call_args[0][0]




