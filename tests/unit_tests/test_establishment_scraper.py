import pytest

from unittest.mock import MagicMock, patch, ANY
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from errors.establishment_scraping_error import ScrapingError
from interfaces.establishment_scraper import CNESScraper


@pytest.fixture
def mock_driver():
    # Create a mock driver with all the necessary methods and properties
    driver = MagicMock()
    return driver


@pytest.fixture
def cnes_scraper():
    with patch('interfaces.establishment_scraper.webdriver.Chrome'), \
         patch('interfaces.establishment_scraper.ChromeDriverManager'):
        scraper = CNESScraper()
        # Reduce timeout for faster tests
        scraper.TIMEOUT_DEFAULT = 1
        return scraper


class TestCNESScraper:
    
    @patch('interfaces.establishment_scraper.webdriver.Chrome')
    @patch('interfaces.establishment_scraper.Service')
    @patch('interfaces.establishment_scraper.ChromeDriverManager')
    def test_validate_online_with_cnes_success(self, mock_manager, mock_service, mock_chrome, cnes_scraper, mock_driver):
        """Test successful establishment validation using CNES code"""
        # Setup
        mock_chrome.return_value = mock_driver
        cnes_scraper._search_by_cnes = MagicMock(return_value=True)
        cnes_scraper._check_services = MagicMock(return_value=True)
        
        # Execute
        result = cnes_scraper.validate_online("1234567", "TEST HOSPITAL")
        
        # Assert
        assert result is True
        cnes_scraper._search_by_cnes.assert_called_once_with(mock_driver, "1234567")
        cnes_scraper._check_services.assert_called_once_with(mock_driver)
        mock_driver.quit.assert_called_once()
    
    @patch('interfaces.establishment_scraper.webdriver.Chrome')
    @patch('interfaces.establishment_scraper.Service')
    @patch('interfaces.establishment_scraper.ChromeDriverManager')
    def test_validate_online_fallback_to_name(self, mock_manager, mock_service, mock_chrome, cnes_scraper, mock_driver):
        """Test establishment validation falling back to name search when CNES search fails"""
        # Setup
        mock_chrome.return_value = mock_driver
        cnes_scraper._search_by_cnes = MagicMock(return_value=False)
        cnes_scraper._search_by_name = MagicMock(return_value=True)
        cnes_scraper._check_services = MagicMock(return_value=True)
        
        # Execute
        result = cnes_scraper.validate_online("1234567", "TEST HOSPITAL")
        
        # Assert
        assert result is True
        cnes_scraper._search_by_cnes.assert_called_once_with(mock_driver, "1234567")
        cnes_scraper._search_by_name.assert_called_once_with(mock_driver, "TEST HOSPITAL")
        cnes_scraper._check_services.assert_called_once_with(mock_driver)
    
    @patch('interfaces.establishment_scraper.webdriver.Chrome')
    @patch('interfaces.establishment_scraper.Service')
    @patch('interfaces.establishment_scraper.ChromeDriverManager')
    def test_validate_online_not_found(self, mock_manager, mock_service, mock_chrome, cnes_scraper, mock_driver):
        """Test case when establishment is not found"""
        # Setup
        mock_chrome.return_value = mock_driver
        cnes_scraper._search_by_cnes = MagicMock(return_value=False)
        cnes_scraper._search_by_name = MagicMock(return_value=False)
        
        # Execute
        result = cnes_scraper.validate_online("1234567", "TEST HOSPITAL")
        
        # Assert
        assert result is False
        mock_driver.quit.assert_called_once()
    
    @patch('interfaces.establishment_scraper.webdriver.Chrome')
    @patch('interfaces.establishment_scraper.Service')
    @patch('interfaces.establishment_scraper.ChromeDriverManager')
    def test_validate_online_with_selenium_exception(self, mock_manager, mock_service, mock_chrome, cnes_scraper, mock_driver):
        """Test error handling when Selenium raises an exception"""
        # Setup
        mock_chrome.return_value = mock_driver
        cnes_scraper._search_by_cnes = MagicMock(side_effect=TimeoutException("Timeout"))
        
        # Execute and Assert
        with pytest.raises(ScrapingError) as excinfo:
            cnes_scraper.validate_online("1234567", "TEST HOSPITAL")
        
        # Check exception details
        assert "Operação demorou mais do que o esperado" in str(excinfo.value)
        mock_driver.quit.assert_called_once()
    
    @patch('interfaces.establishment_scraper.webdriver.Chrome')
    @patch('interfaces.establishment_scraper.Service')
    @patch('interfaces.establishment_scraper.ChromeDriverManager')
    def test_driver_quit_exception_handling(self, mock_manager, mock_service, mock_chrome, cnes_scraper, mock_driver):
        """Test handling of exceptions when quitting the driver"""
        # Setup
        mock_chrome.return_value = mock_driver
        mock_driver.quit.side_effect = Exception("Driver quit error")
        cnes_scraper._search_by_cnes = MagicMock(side_effect=Exception("Test error"))
        
        # Execute and Assert - should not raise exception from driver.quit()
        with pytest.raises(ScrapingError):
            cnes_scraper.validate_online("1234567", "TEST HOSPITAL")
        
        # Verify quit was called even though it raised an exception
        mock_driver.quit.assert_called_once()
    
    def test_search_by_cnes_success(self, cnes_scraper, mock_driver):
        """Test successful search by CNES"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(return_value=True)
        
        # Execute
        result = cnes_scraper._search_by_cnes(mock_driver, "1234567")
        
        # Assert
        assert result is True
        mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search=1234567")
        cnes_scraper._wait_for_element.assert_called_once_with(
            mock_driver, 
            "body > div.layout > main > div > div.col-md-12.ng-scope > div > div:nth-child(9) > table > tbody > tr > td:nth-child(8) > a > span", 
            ANY
        )
    
    def test_search_by_cnes_failure(self, cnes_scraper, mock_driver):
        """Test CNES search that fails"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(side_effect=Exception("Element not found"))
        
        # Execute
        result = cnes_scraper._search_by_cnes(mock_driver, "1234567")
        
        # Assert
        assert result is False
    
    def test_search_by_name_success(self, cnes_scraper, mock_driver):
        """Test successful search by name"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(return_value=True)
        
        # Execute
        result = cnes_scraper._search_by_name(mock_driver, "TEST HOSPITAL")
        
        # Assert
        assert result is True
        mock_driver.get.assert_called_once_with("https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search=TEST%20HOSPITAL")
    
    def test_search_by_name_failure(self, cnes_scraper, mock_driver):
        """Test name search that fails"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(side_effect=Exception("Element not found"))
        
        # Execute
        result = cnes_scraper._search_by_name(mock_driver, "TEST HOSPITAL")
        
        # Assert
        assert result is False
    
    def test_check_services_success(self, cnes_scraper, mock_driver):
        """Test successful service check when required service codes are found"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(return_value=True)
        cnes_scraper._click_element = MagicMock()
        
        # Mock the rows with service codes
        mock_row1 = MagicMock()
        mock_row1.find_element.return_value.text = "159"  # One of the required codes
        mock_row2 = MagicMock()
        mock_row2.find_element.return_value.text = "123"  # Not a required code
        
        mock_driver.find_elements.return_value = [mock_row1, mock_row2]
        
        # Execute
        result = cnes_scraper._check_services(mock_driver)
        
        # Assert
        assert result is True
        assert cnes_scraper._click_element.call_count == 3  # Click on 3 elements during the process
        mock_driver.find_elements.assert_called_once()
    
    def test_check_services_no_required_codes(self, cnes_scraper, mock_driver):
        """Test service check when no required service codes are found"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(return_value=True)
        cnes_scraper._click_element = MagicMock()
        
        # Mock the rows without the required service codes
        mock_row1 = MagicMock()
        mock_row1.find_element.return_value.text = "123"  # Not a required code
        mock_row2 = MagicMock()
        mock_row2.find_element.return_value.text = "456"  # Not a required code
        
        mock_driver.find_elements.return_value = [mock_row1, mock_row2]
        
        # Execute
        result = cnes_scraper._check_services(mock_driver)
        
        # Assert
        assert result is False
        assert cnes_scraper._click_element.call_count == 3  # Click on 3 elements during the process
        mock_driver.find_elements.assert_called_once()
    
    def test_check_services_element_not_found(self, cnes_scraper, mock_driver):
        """Test service check when an element is not found"""
        # Setup
        cnes_scraper._wait_for_element = MagicMock(side_effect=[True, False])  # First element found, second not found
        cnes_scraper._click_element = MagicMock()
        
        # Execute and Assert
        with pytest.raises(ScrapingError) as excinfo:
            cnes_scraper._check_services(mock_driver)
        
        # Check exception details
        assert "Link 'Serviços' não encontrado na página do estabelecimento" in str(excinfo.value)
    
    def test_wait_for_element_success(self, cnes_scraper, mock_driver):
        """Test successful wait for element"""
        # Setup
        with patch('interfaces.establishment_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = True
            
            # Execute
            result = cnes_scraper._wait_for_element(mock_driver, "test-selector", ANY)
            
            # Assert
            assert result is True
    
    def test_wait_for_element_timeout(self, cnes_scraper, mock_driver):
        """Test timeout while waiting for element"""
        # Setup
        with patch('interfaces.establishment_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("Timeout")
            
            # Execute and Assert
            with pytest.raises(TimeoutException) as excinfo:
                cnes_scraper._wait_for_element(mock_driver, "test-selector", ANY)
            
            # Check exception details
            assert "Timeout esperando pelo elemento" in str(excinfo.value)
    
    def test_click_element_success(self, cnes_scraper, mock_driver):
        """Test successful element click"""
        # Setup
        mock_element = MagicMock()
        with patch('interfaces.establishment_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = mock_element
            
            # Execute
            cnes_scraper._click_element(mock_driver, "test-selector")
            
            # Assert
            mock_element.click.assert_called_once()
    
    def test_click_element_not_found(self, cnes_scraper, mock_driver):
        """Test error when element to click is not found"""
        # Setup
        with patch('interfaces.establishment_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = NoSuchElementException("Element not found")
            
            # Execute and Assert
            with pytest.raises(NoSuchElementException) as excinfo:
                cnes_scraper._click_element(mock_driver, "test-selector")
            
            # Check exception details
            assert "Elemento não encontrado" in str(excinfo.value)
    
    def test_click_element_timeout(self, cnes_scraper, mock_driver):
        """Test timeout when waiting for element to be clickable"""
        # Setup
        with patch('interfaces.establishment_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("Timeout")
            
            # Execute and Assert
            with pytest.raises(TimeoutException) as excinfo:
                cnes_scraper._click_element(mock_driver, "test-selector")
            
            # Check exception details
            assert "Elemento não clicável" in str(excinfo.value)