import pytest
import json
import time
import threading
import logging
from flask import Flask
from werkzeug.serving import make_server
import requests
import sseclient
import uuid

from controllers.controller import app, run_api
from core.services.core_service import Services
from repositories.establishment_repository import EstablishmentRepository
from errors.database_error import DatabaseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestServer:
    """Test server class to run the Flask app in a separate thread during tests"""
    
    def __init__(self, app, host='192.168.1.5', port=5000):
        self.server = make_server(host, port, app)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        
    def start(self):
        self.server_thread.start()
        logger.info(f"Test server started at {self.url}")
        # Give the server time to start
        time.sleep(1)
        
    def stop(self):
        self.server.shutdown()
        self.server_thread.join()
        logger.info("Test server stopped")


@pytest.fixture(scope="module")
def test_server():
    """Fixture to start and stop the test server for all tests"""
    server = TestServer(app)
    server.start()
    yield server
    server.stop()


class SSEListener:
    """Helper class to listen to SSE events"""
    
    def __init__(self, url):
        self.url = url
        self.events = []
        self.progress_events = []
        self.result_event = None
        self.error_event = None
        self.thread = None
        self.running = False
        
    def start_listening(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen)
        self.thread.daemon = True
        self.thread.start()
        
    def stop_listening(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        
    def _listen(self):
        try:
            response = requests.get(self.url, stream=True)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if not self.running:
                    break
                    
                self.events.append(event)
                
                if event.event == "progress":
                    self.progress_events.append(json.loads(event.data))
                elif event.event == "result":
                    self.result_event = json.loads(event.data)
                elif event.event == "error":
                    self.error_event = json.loads(event.data)
        except Exception as e:
            logger.error(f"Error in SSE listener: {e}")


@pytest.fixture
def health_endpoint(test_server):
    """Fixture that returns the health endpoint URL"""
    return f"{test_server.url}/health"


@pytest.fixture
def process_endpoint(test_server):
    """Fixture that returns the main processing endpoint URL"""
    return f"{test_server.url}/"


@pytest.fixture
def events_endpoint(test_server):
    """Fixture that returns the SSE events endpoint URL"""
    return f"{test_server.url}/events"


class TestHealthEndpoint:
    """Tests for the health endpoint"""
    
    def test_health_check_success(self, health_endpoint):
        """Test that health check returns 200 when database is connected"""
        response = requests.get(health_endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestProcessEndpoint:
    """Tests for the main processing endpoint"""
    
    def test_process_eligible_professional(self, process_endpoint, events_endpoint):
        """Test processing an eligible professional with success case data"""
        # Prepare request data
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        result = response.json()
        assert result["status"] == "processing"
        assert "request_id" in result
        
        # Connect to SSE endpoint to get real-time updates
        request_id = result["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for processing to complete (adjust timeout as needed)
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.result_event or listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got a result and not an error
        assert listener.error_event is None, f"Got error: {listener.error_event}"
        assert listener.result_event is not None, "No result received within timeout"
        
        # Check the result
        result = listener.result_event
        assert result["name"] == "EDGARD KINDERMANN"
        assert result["status"] == "ELIGIBLE"
        assert result["valid_months"] >= 48
        assert "details" in result
        assert "semesters_40" in result["details"]
        assert "semesters_30" in result["details"]
        assert "semesters_20" in result["details"]
        
        # Check progress events
        assert len(listener.progress_events) > 0
        # Check that we got progress updates for each step
        steps_reported = set(event["step"] for event in listener.progress_events)
        assert steps_reported.issuperset({1, 2, 3})
        
        # Check final progress event
        final_progress = next((event for event in reversed(listener.progress_events) 
                              if event["status"] == "completed"), None)
        assert final_progress is not None
        assert final_progress["percentage"] == 100
        
    def test_process_not_eligible_professional(self, process_endpoint, events_endpoint):
        """Test processing a professional who is not eligible"""
        # Prepare request data
        data = {
            "cpf": "04729738519",
            "name": "Priscila Maciel"
        }
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        result = response.json()
        assert result["status"] == "processing"
        assert "request_id" in result
        
        # Connect to SSE endpoint to get real-time updates
        request_id = result["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for processing to complete
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.result_event or listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got a result and not an error
        assert listener.error_event is None, f"Got error: {listener.error_event}"
        assert listener.result_event is not None, "No result received within timeout"
        
        # Check the result
        result = listener.result_event
        assert result["name"] == "PRISCILA MACIEL"
        assert result["status"] == "NOT ELIGIBLE"
        assert result["valid_months"] < 48
        assert result["pending_months"] > 0
        
    def test_process_professional_not_found(self, process_endpoint, events_endpoint):
        """Test processing a professional who doesn't exist in the system"""
        # Prepare request data
        data = {
            "cpf": "13012295631",
            "name": "xyvictor tadeu"
        }
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        result = response.json()
        assert result["status"] == "processing"
        assert "request_id" in result
        
        # Connect to SSE endpoint to get real-time updates
        request_id = result["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for processing to complete
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.result_event or listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error and not a result
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # Check the error
        error = listener.error_event
        assert "error" in error
        assert "Profissional não encontrado" in error["error"]
        
    def test_invalid_input_data(self, process_endpoint):
        """Test processing with invalid input data"""
        # Case 1: Missing required field
        data = {"cpf": "1544356943"}
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 400
        
        # Case 2: Empty fields
        data = {"cpf": "", "name": ""}
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 400
        
        # Case 3: Invalid data types
        data = {"cpf": 12345, "name": ["invalid"]}
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 400


class TestSSEFunctionality:
    """Tests for the SSE functionality"""
    
    def test_create_new_sse_client(self, events_endpoint):
        """Test creating a new SSE client without providing a request_id"""
        # This should create a new client and return a stream
        response = requests.get(events_endpoint, stream=True)
        assert response.status_code == 200
        print(response.headers.get('Content-Type'))
        assert 'text/event-stream' in response.headers.get('Content-Type')
        
        # Close the connection
        response.close()
          
    
class TestErrorHandling:
    """Tests for error handling scenarios"""
    
    def test_database_error_handling(self, monkeypatch, health_endpoint):
        """Test handling of database errors by patching the ping method"""
        # Patch the ping method to raise a DatabaseError
        def mock_ping_error(self):
            raise DatabaseError("Mocked database error")
            
        monkeypatch.setattr(EstablishmentRepository, "ping", mock_ping_error)
        
        # Now the health check should report an unhealthy status
        response = requests.get(health_endpoint)
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert "error" in data
        
    def test_external_service_error_handling(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of external service errors by simulating scraper failures"""
        # Use a valid request that would normally succeed
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Patch the CSV scraper to raise an error
        def mock_get_csv_data(*args, **kwargs):
            from errors.csv_scraping_error import CSVScrapingError
            raise CSVScrapingError(
                "Simulated external service error",
                {"test": "External service unavailable"}
            )
            
        from interfaces.csv_scraper import CSVScraper
        monkeypatch.setattr(CSVScraper, "get_csv_data", mock_get_csv_data)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for processing to complete
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Should get an external service error
        assert listener.error_event is not None
        assert "Profissional não encontrado" in listener.error_event["error"]
        assert listener.error_event["status_code"] == 404
    
    def test_establishment_validation_error(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of establishment validation errors"""
        # Prepare request data with valid format
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Patch the establishment validator to raise an EstablishmentValidationError
        def mock_check_establishment(*args, **kwargs):
            from errors.establishment_validator_error import EstablishmentValidationError
            raise EstablishmentValidationError(
                "Erro na validação do estabelecimento",
                {"test": "Simulated validation error"}
            )
            
        from core.services.establishment_validator import EstablishmentValidator
        monkeypatch.setattr(EstablishmentValidator, "check_establishment", mock_check_establishment)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for error event
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error event
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # Check the error
        error = listener.error_event
        assert "error" in error
        assert "Erro na validação do estabelecimento" in error["error"]
        assert listener.error_event["status_code"] == 422
    
    def test_data_processing_error(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of data processing errors"""
        # Prepare request data
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Patch the data processor to raise a DataProcessingError
        def mock_process_csv(*args, **kwargs):
            from errors.data_processing_error import DataProcessingError
            raise DataProcessingError(
                "Erro ao processar dados do CSV",
                {"source": "test", "details": "Simulated processing error"}
            )
            
        from core.services.data_processor import DataProcessor
        monkeypatch.setattr(DataProcessor, "process_csv", mock_process_csv)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for error event
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error event
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # Check the error
        error = listener.error_event
        assert "error" in error
        assert "Erro ao processar dados do CSV" in error["error"]
        assert listener.error_event["status_code"] == 422
    
    def test_sse_invalid_request_id(self, events_endpoint):
        """Test SSE endpoint with an invalid request ID"""
        # Connect to SSE endpoint with a non-existing request ID
        invalid_id = "non-existing-request-id"
        sse_url = f"{events_endpoint}?request_id={invalid_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # This should create a new client with the provided ID
        response = requests.get(sse_url, stream=True)
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers.get('Content-Type')
        
        # Close the connection
        response.close()
    
    def test_unexpected_exception(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of unexpected exceptions during processing"""
        # Prepare request data
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Patch run_services to raise an unexpected exception
        def mock_run_services(*args, **kwargs):
            raise Exception("Unexpected runtime error")
            
        from core.services.core_service import Services
        monkeypatch.setattr(Services, "run_services", mock_run_services)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for error event
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error event
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # Check the error
        error = listener.error_event
        assert "error" in error
        assert "Processing failed" in error["error"]
        assert error["status_code"] == 500
    
    def test_scraping_error_handling(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of scraping errors from the establishment validator"""
        # Prepare request data
        data = {
            "cpf": "21510493883",
            "name": "Samir Lisak"
        }
        
        # Patch the validate_online method to raise a ScrapingError
        def mock_validate_online(*args, **kwargs):
            from errors.establishment_scraping_error import ScrapingError
            raise ScrapingError(
                "Erro ao acessar o site do CNES",
                {"details": "Simulated scraping error"}
            )
            
        from interfaces.establishment_scraper import CNESScraper
        monkeypatch.setattr(CNESScraper, "validate_online", mock_validate_online)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for error event
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error event
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # The error should be wrapped in an ExternalServiceError
        error = listener.error_event
        assert "error" in error
        assert "Erro ao acessar o site do CNES" in error["error"]
        assert listener.error_event["status_code"] == 503
    
    def test_invalid_csv_format(self, monkeypatch, process_endpoint, events_endpoint):
        """Test handling of invalid CSV format"""
        # Prepare request data
        data = {
            "cpf": "01544356943",
            "name": "Edgard Kindermann"
        }
        
        # Return an invalid CSV format
        def mock_get_csv_data(*args, **kwargs):
            return "invalid,csv,format\nwithout,proper,headers"
            
        from interfaces.csv_scraper import CSVScraper
        monkeypatch.setattr(CSVScraper, "get_csv_data", mock_get_csv_data)
        
        # Send the processing request
        response = requests.post(process_endpoint, json=data)
        assert response.status_code == 202
        
        request_id = response.json()["request_id"]
        sse_url = f"{events_endpoint}?request_id={request_id}"
        
        # Add a small delay to ensure error event isn't missed
        time.sleep(0.5)
        
        # Start listening for SSE events
        listener = SSEListener(sse_url)
        listener.start_listening()
        
        # Wait for error event
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if listener.error_event:
                break
            time.sleep(1)
            
        listener.stop_listening()
        
        # Assert we got an error event
        assert listener.result_event is None, "Got unexpected result"
        assert listener.error_event is not None, "No error received within timeout"
        
        # The error should be about missing columns or invalid format
        error = listener.error_event
        assert "error" in error
        assert "formato de dados inválido" in error["error"].lower() or "missing" in error["error"].lower()
    
    # def test_concurrent_requests(self, process_endpoint, events_endpoint):
    #     """Test handling of concurrent requests to the same endpoint"""
    #     # Prepare two identical requests
    #     data = {
    #         "cpf": "01544356943",
    #         "name": "Edgard Kindermann"
    #     }
        
    #     # Send two concurrent requests
    #     response1 = requests.post(process_endpoint, json=data)
    #     response2 = requests.post(process_endpoint, json=data)
        
    #     assert response1.status_code == 202
    #     assert response2.status_code == 202
        
    #     # Each request should get a unique request_id
    #     request_id1 = response1.json()["request_id"]
    #     request_id2 = response2.json()["request_id"]
        
    #     assert request_id1 != request_id2
        
    #     # Connect to SSE endpoint for both requests
    #     sse_url1 = f"{events_endpoint}?request_id={request_id1}"
    #     sse_url2 = f"{events_endpoint}?request_id={request_id2}"
        
    #     # Add a small delay to ensure error event isn't missed
    #     time.sleep(0.5)
        
    #     # Start listening for SSE events for both requests
    #     listener1 = SSEListener(sse_url1)
    #     listener2 = SSEListener(sse_url2)
        
    #     listener1.start_listening()
    #     listener2.start_listening()
        
    #     # Wait for processing to complete for both requests
    #     max_wait = 60  # seconds
    #     start_time = time.time()
        
    #     while time.time() - start_time < max_wait:
    #         if (listener1.result_event or listener1.error_event) and \
    #            (listener2.result_event or listener2.error_event):
    #             break
    #         time.sleep(1)
            
    #     listener1.stop_listening()
    #     listener2.stop_listening()
        
    #     # Both requests should complete successfully or with an error
    #     assert (listener1.result_event is not None or listener1.error_event is not None), \
    #         "First request did not complete within timeout"
    #     assert (listener2.result_event is not None or listener2.error_event is not None), \
    #         "Second request did not complete within timeout"
        
    #     # If both succeeded, they should have the same result (same input data)
    #     if listener1.result_event and listener2.result_event:
    #         assert listener1.result_event["name"] == listener2.result_event["name"]
    #         assert listener1.result_event["status"] == listener2.result_event["status"]
    
    def test_nonexistent_endpoint(self, test_server):
        """Test accessing a non-existent endpoint"""
        nonexistent_url = f"{test_server.url}/nonexistent"
        response = requests.get(nonexistent_url)
        
        # Should return 404
        assert response.status_code == 404