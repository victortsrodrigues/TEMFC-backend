import pytest
import json

from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

from src.interfaces.csv_scraper import CSVScraper
from errors.csv_scraping_error import CSVScrapingError

class TestCSVScraper:
    """Test suite for CSVScraper class"""

    @pytest.fixture
    def csv_scraper(self):
        """Create a CSVScraper instance with mocked webdriver"""
        with patch('src.interfaces.csv_scraper'):
            scraper = CSVScraper()
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

    def test_init(self, csv_scraper):
        """Test CSVScraper initialization"""
        assert csv_scraper.logger is not None
        assert csv_scraper.options is not None
        

    def test_search_by_cpf_success(self, csv_scraper, mock_driver):
        """Test successful search by CPF"""
        # Arrange
        with patch.object(csv_scraper, '_wait_for_element', return_value=True) as mock_wait:
            # Act
            result = csv_scraper._search_by_cpf(mock_driver, "12345678900")
            
            # Assert
            assert result is True
            mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search=12345678900")
            mock_wait.assert_called_once()

    def test_search_by_cpf_failure(self, csv_scraper, mock_driver):
        """Test failed search by CPF"""
        # Arrange
        with patch.object(csv_scraper, '_wait_for_element', return_value=False) as mock_wait:
            # Act
            result = csv_scraper._search_by_cpf(mock_driver, "12345678900")
            
            # Assert
            assert result is False
            mock_driver.get.assert_called_once()
            mock_wait.assert_called_once()

    def test_search_by_cpf_exception(self, csv_scraper, mock_driver):
        """Test exception handling during search by CPF"""
        # Arrange
        mock_driver.get.side_effect = Exception("Error accessing URL")
        
        # Act
        result = csv_scraper._search_by_cpf(mock_driver, "12345678900")
        
        # Assert
        assert result is False
        mock_driver.get.assert_called_once()

    def test_search_by_name_success(self, csv_scraper, mock_driver):
        """Test successful search by name"""
        # Arrange
        with patch.object(csv_scraper, '_wait_for_element', return_value=True) as mock_wait:
            # Act
            result = csv_scraper._search_by_name(mock_driver, "TEST NAME")
            
            # Assert
            assert result is True
            mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search=TEST%20NAME")
            mock_wait.assert_called_once()

    def test_search_by_name_failure(self, csv_scraper, mock_driver):
        """Test failed search by name"""
        # Arrange
        with patch.object(csv_scraper, '_wait_for_element', return_value=False) as mock_wait:
            # Act
            result = csv_scraper._search_by_name(mock_driver, "TEST NAME")
            
            # Assert
            assert result is False
            mock_driver.get.assert_called_once()
            mock_wait.assert_called_once()

    def test_search_by_name_exception(self, csv_scraper, mock_driver):
        """Test exception handling during search by name"""
        # Arrange
        mock_driver.get.side_effect = Exception("Error accessing URL")
        
        # Act
        result = csv_scraper._search_by_name(mock_driver, "TEST NAME")
        
        # Assert
        assert result is False
        mock_driver.get.assert_called_once()

    def test_intercept_data_success(self, csv_scraper, mock_driver):
        """Test successful data interception"""
        # Arrange
        with patch.object(csv_scraper, '_click_element') as mock_click:
            with patch.object(csv_scraper, '_wait_for_element', return_value=True) as mock_wait:
                with patch.object(csv_scraper, '_wait_for_intercepted_data', return_value="CSV DATA") as mock_intercept:
                    # Act
                    result = csv_scraper._intercept_data(mock_driver)
                    
                    # Assert
                    assert result == "CSV DATA"
                    assert mock_click.call_count == 2
                    mock_wait.assert_called_once()
                    mock_intercept.assert_called_once()

    def test_intercept_data_export_button_not_found(self, csv_scraper, mock_driver):
        """Test when CSV export button is not found"""
        # Arrange
        with patch.object(csv_scraper, '_click_element') as mock_click:
            with patch.object(csv_scraper, '_wait_for_element', return_value=False) as mock_wait:
                # Act & Assert
                with pytest.raises(CSVScrapingError) as exc_info:
                    csv_scraper._intercept_data(mock_driver)
                
                # Verify exception details
                assert "CSV export functionality not available" in str(exc_info.value)
                mock_click.assert_called_once()
                mock_wait.assert_called_once()

    def test_intercept_data_no_data_intercepted(self, csv_scraper, mock_driver):
        """Test when no data is intercepted"""
        # Arrange
        with patch.object(csv_scraper, '_click_element') as mock_click:
            with patch.object(csv_scraper, '_wait_for_element', return_value=True) as mock_wait:
                with patch.object(csv_scraper, '_wait_for_intercepted_data', return_value=None) as mock_intercept:
                    # Act & Assert
                    with pytest.raises(CSVScrapingError) as exc_info:
                        csv_scraper._intercept_data(mock_driver)
                    
                    # Verify exception details
                    assert "Failed to retrieve CSV data" in str(exc_info.value)
                    assert mock_click.call_count == 2
                    mock_wait.assert_called_once()
                    mock_intercept.assert_called_once()

    def test_intercept_data_element_not_found(self, csv_scraper, mock_driver):
        """Test handling of NoSuchElementException during data interception"""
        # Arrange
        mock_click_side_effect = [None, NoSuchElementException("Element not found")]
        with patch.object(csv_scraper, '_click_element', side_effect=mock_click_side_effect):
            with patch.object(csv_scraper, '_wait_for_element', return_value=True) as mock_wait:
                # Act & Assert
                with pytest.raises(CSVScrapingError) as exc_info:
                    csv_scraper._intercept_data(mock_driver)
                
                # Verify exception details
                assert "Required element not found during data export" in str(exc_info.value)
                mock_wait.assert_called_once()

    def test_wait_for_element_success(self, csv_scraper, mock_driver):
        """Test successful element wait"""
        # Arrange
        mock_wait = MagicMock()
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = csv_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is True
            mock_wait_class.assert_called_once_with(mock_driver, 5)

    def test_wait_for_element_timeout(self, csv_scraper, mock_driver):
        """Test element wait timeout"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Timeout")
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = csv_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is False
            mock_wait_class.assert_called_once()

    def test_wait_for_element_exception(self, csv_scraper, mock_driver):
        """Test element wait general exception"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = Exception("General error")
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait) as mock_wait_class:
            # Act
            result = csv_scraper._wait_for_element(mock_driver, "test-selector", By.CSS_SELECTOR)
            
            # Assert
            assert result is False
            mock_wait_class.assert_called_once()

    def test_click_element_success(self, csv_scraper, mock_driver):
        """Test successful element click"""
        # Arrange
        mock_element = MagicMock()
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_element
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait):
            # Act
            csv_scraper._click_element(mock_driver, "test-selector")
            
            # Assert
            mock_element.click.assert_called_once()

    def test_click_element_not_found(self, csv_scraper, mock_driver):
        """Test element click when element not found"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = NoSuchElementException("Element not found")
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait):
            # Act & Assert
            with pytest.raises(NoSuchElementException) as excinfo:
                csv_scraper._click_element(mock_driver, "test-selector")
                
        assert "Element not found" in str(excinfo.value)

    def test_click_element_timeout(self, csv_scraper, mock_driver):
        """Test element click timeout"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Timeout")
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait):
            # Act & Assert
            with pytest.raises(TimeoutException) as excinfo:
                csv_scraper._click_element(mock_driver, "test-selector")
                
        assert "Element not clickable" in str(excinfo.value)

    def test_click_element_general_exception(self, csv_scraper, mock_driver):
        """Test element click general exception"""
        # Arrange
        mock_wait = MagicMock()
        mock_wait.until.side_effect = Exception("General error")
        with patch('src.interfaces.csv_scraper.WebDriverWait', return_value=mock_wait):
            # Act & Assert
            with pytest.raises(Exception) as excinfo:
                csv_scraper._click_element(mock_driver, "test-selector")
                
        assert "General error" in str(excinfo.value)

    def test_wait_for_intercepted_data_success(self, csv_scraper, mock_driver, mock_successful_request):
        """Test successful intercepted data wait"""
        # Arrange
        mock_driver.requests = [mock_successful_request]
        with patch.object(csv_scraper, '_json_to_csv', return_value="CSV DATA") as mock_convert:
            # Act
            result = csv_scraper._wait_for_intercepted_data(mock_driver)
            
            # Assert
            assert result == "CSV DATA"
            mock_convert.assert_called_once()

    def test_wait_for_intercepted_data_timeout(self, csv_scraper, mock_driver):
        """Test intercepted data wait timeout"""
        # Arrange
        mock_driver.requests = []
        with patch('src.interfaces.csv_scraper.time.sleep') as mock_sleep:
            with patch('src.interfaces.csv_scraper.time.time', side_effect=[0, 1, 11]):  # Simulate timeout
                # Act
                result = csv_scraper._wait_for_intercepted_data(mock_driver)
                
                # Assert
                assert result is None
                mock_sleep.assert_called_once()

    def test_wait_for_intercepted_data_exception(self, csv_scraper, mock_driver, mock_successful_request):
        """Test intercepted data processing exception"""
        # Arrange
        mock_driver.requests = [mock_successful_request]
        with patch.object(csv_scraper, '_json_to_csv', side_effect=Exception("Processing error")) as mock_convert:
            # Act & Assert
            with pytest.raises(CSVScrapingError) as exc_info:
                csv_scraper._wait_for_intercepted_data(mock_driver)
            
            # Verify exception details
            assert "Failed to process intercepted data" in str(exc_info.value)
            mock_convert.assert_called_once()

    def test_json_to_csv_success(self, csv_scraper):
        """Test successful JSON to CSV conversion"""
        # Arrange
        json_str = json.dumps({
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
        })
        
        # Act
        result = csv_scraper._json_to_csv(json_str)
        
        # Assert
        assert "NOME;SEXO;CNS;COMP.;IBGE;UF;MUNICIPIO;CBO" in result
        assert "TEST PROFESSIONAL;M;123456789012345;01/2023;123456;SP;SAO PAULO;225125" in result

    def test_json_to_csv_empty_json(self, csv_scraper):
        """Test JSON to CSV conversion with empty JSON"""
        # Arrange
        json_str = json.dumps({})
        
        # Act & Assert
        with pytest.raises(CSVScrapingError) as exc_info:
            csv_scraper._json_to_csv(json_str)
        
        # Verify exception details
        assert "Empty or invalid JSON data received" in str(exc_info.value)

    def test_json_to_csv_missing_fields(self, csv_scraper):
        """Test JSON to CSV conversion with missing required fields"""
        # Arrange
        json_str = json.dumps({
            "sexo": "M",  # Missing nome field
            "cns": "123456789012345",
            "vinculos": []
        })
        
        # Act & Assert
        with pytest.raises(CSVScrapingError) as exc_info:
            csv_scraper._json_to_csv(json_str)
        
        # Verify exception details
        assert "Incomplete professional data received" in str(exc_info.value)

    def test_json_to_csv_invalid_json(self, csv_scraper):
        """Test JSON to CSV conversion with invalid JSON"""
        # Arrange
        json_str = "Invalid JSON"
        
        # Act & Assert
        with pytest.raises(CSVScrapingError) as exc_info:
            csv_scraper._json_to_csv(json_str)
        
        # Verify exception details
        assert "Failed to parse JSON data" in str(exc_info.value)

    def test_json_to_csv_general_exception(self, csv_scraper):
        """Test JSON to CSV conversion with general exception"""
        # Arrange
        json_str = json.dumps({
            "nome": "TEST PROFESSIONAL",
            "sexo": "M",
            "cns": "123456789012345",
            "vinculos": [{"nuComp": "01/2023"}]
        })
        
        with patch('src.interfaces.csv_scraper.StringIO', side_effect=Exception("StringIO error")):
            # Act & Assert
            with pytest.raises(CSVScrapingError) as exc_info:
                csv_scraper._json_to_csv(json_str)
            
            # Verify exception details
            assert "Failed to convert JSON to CSV format" in str(exc_info.value)

