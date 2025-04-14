import pytest
import json
import time
import threading
import logging
from werkzeug.serving import make_server
import requests
import sseclient

from src.errors.csv_scraping_error import CSVScrapingError
from src.errors.establishment_validator_error import EstablishmentValidationError
from src.errors.data_processing_error import DataProcessingError

from src.app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = '127.0.0.1'
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"

# ------------------ Monkeypatch run_services ------------------
@pytest.fixture
def stub_run_services(monkeypatch, app):
    """
    Substitui Services.run_services para publicar eventos imediatos sem invocar Selenium ou DB.
    """
    from src.core.services.core_service import Services
    from src.utils.sse_manager import sse_manager
    from src.errors.not_found_error import NotFoundError

    def fake_run_services(self, body, request_id=None):
        cpf = body.get('cpf')
        name = body.get('name')
        # Passo de progresso inicial
        if request_id:
            sse_manager.publish_progress(request_id, 1, "Iniciando processamento", 0, "in_progress")
        # Decide comportamento por CPF
        if cpf == '11111111111':  # elegível
            valid_months = 60
        elif cpf == '22222222222':  # não elegível
            valid_months = 30
        elif cpf == '33333333333':  # não encontrado
            error_data = {'error': 'Profissional não encontrado', 'status_code': 404}
            sse_manager.publish_event(request_id, 'error', error_data)
            sse_manager.publish_progress(request_id, 3, f"Error: {error_data['error']}", None, 'error')
            raise NotFoundError("Profissional não encontrado")
        else:
            valid_months = 0
        # Publica resultado
        result = {
            'name': name,
            'valid_months': valid_months,
            'status': 'ELIGIBLE' if valid_months >= 48 else 'NOT ELIGIBLE',
            'pending_months': max(0, 48 - valid_months)
        }
        sse_manager.publish_event(request_id, 'result', result)
        sse_manager.publish_progress(request_id, 3, "Processo concluído!", 100, 'completed')
        return valid_months

    monkeypatch.setattr(Services, 'run_services', fake_run_services)
    
    app.services = Services()
    app.sse_manager = sse_manager

@pytest.fixture(scope='module')
def app():
    """Create and configure a Flask app for testing."""
    # Create the Flask application instance with test configuration
    test_app = create_app({
        'TESTING': True,
    })
    return test_app

class IntegrationTestServer:
    def __init__(self, app, host=HOST, port=PORT):
        self.server = make_server(host, port, app, threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        time.sleep(1)

    def stop(self):
        self.server.shutdown()
        self.thread.join()

@pytest.fixture(scope='module')
def test_server(app):
    srv = IntegrationTestServer(app)
    srv.start()
    yield srv
    srv.stop()

@pytest.fixture
def health_endpoint(test_server):
    return f"{BASE_URL}/health"

@pytest.fixture
def process_endpoint(test_server):
    return f"{BASE_URL}/"

@pytest.fixture
def events_endpoint(test_server):
    return f"{BASE_URL}/events"

class SSEListener:
    def __init__(self, url):
        self.url = url
        self.events = []
        self.progress_events = []
        self.result_event = None
        self.error_event = None
        self.thread = None
        self.running = False
        self.response = None

    def start_listening(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.running = False
        if self.response:
            self.response.close()
        if self.thread:
            self.thread.join(timeout=3)

    def _listen(self):
        try:
            self.response = requests.get(self.url, stream=True, timeout=10)
            client = sseclient.SSEClient(self.response)
            for event in client.events():
                if not self.running:
                    break
                self.events.append(event)
                if event.event == 'progress':
                    self.progress_events.append(json.loads(event.data))
                elif event.event == 'result':
                    self.result_event = json.loads(event.data)
                elif event.event == 'error':
                    self.error_event = json.loads(event.data)
        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            if self.response:
                self.response.close()

# -------------- Health Endpoint --------------

def test_health_success(health_endpoint):
    resp = requests.get(health_endpoint, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

# -------------- Process Eligible --------------

def test_process_eligible_professional(stub_run_services, process_endpoint, events_endpoint):
    data = {"cpf": "11111111111", "name": "Eligible Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.result_event or listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is None
    assert listener.result_event is not None
    result = listener.result_event
    assert result['name'] == 'ELIGIBLE PROFESSIONAL'
    assert result['status'] == 'ELIGIBLE'
    assert result['valid_months'] >= 48
    assert listener.progress_events

# -------------- Process Not Eligible --------------

def test_process_not_eligible_professional(stub_run_services, process_endpoint, events_endpoint):
    data = {"cpf": "22222222222", "name": "Not Eligible Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.result_event or listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is None
    assert listener.result_event is not None
    result = listener.result_event
    assert result['status'] == 'NOT ELIGIBLE'
    assert result['valid_months'] < 48
    assert result['pending_months'] > 0

# -------------- Process Not Found --------------

def test_process_professional_not_found(stub_run_services, process_endpoint, events_endpoint):
    data = {"cpf": "33333333333", "name": "Not Found Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.result_event is None
    assert listener.error_event is not None
    assert 'Profissional não encontrado' in listener.error_event['error']

# -------------- Invalid Input --------------

def test_invalid_input_data(process_endpoint):
    resp = requests.post(process_endpoint, json={"cpf": "123"}, timeout=5)
    assert resp.status_code in (400, 422)

# -------------- SSE Functionality --------------

def test_create_new_sse_client(events_endpoint):
    resp = requests.get(events_endpoint, stream=True, timeout=5)
    assert resp.status_code == 200
    assert 'text/event-stream' in resp.headers.get('Content-Type')
    resp.close()

def test_multiple_sse_connections(events_endpoint):
    conns = []
    for _ in range(3):
        r = requests.get(events_endpoint, stream=True, timeout=5)
        assert r.status_code == 200
        conns.append(r)
    for r in conns:
        r.close()

# -------------- Error Handling (others) --------------

def test_external_service_error(monkeypatch, process_endpoint, events_endpoint):
    monkeypatch.setattr(
        'interfaces.csv_scraper.CSVScraper.get_csv_data',
        lambda *args, **kwargs: (_ for _ in ()).throw(CSVScrapingError('Fail', {}))
    )
    data = {"cpf": "11111111111", "name": "Random Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is not None
    assert listener.error_event['status_code'] == 404


def test_establishment_validation_error(monkeypatch, process_endpoint, events_endpoint):
    # stub CSV
    monkeypatch.setattr(
        'interfaces.csv_scraper.CSVScraper.get_csv_data',
        lambda *args, **kwargs: (
            "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
            "2337545;317130;Test;20;MEDICO DA FAMILIA;202001"
        )
    )
    # stub error
    monkeypatch.setattr(
        'core.services.establishment_validator.EstablishmentValidator.check_establishment',
        lambda *args, **kwargs: (_ for _ in ()).throw(EstablishmentValidationError('Val error', {}))
    )
    data = {"cpf": "11111111111", "name": "Random Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is not None
    assert listener.error_event['status_code'] == 422


def test_data_processing_error(monkeypatch, process_endpoint, events_endpoint):
    # stub CSV
    monkeypatch.setattr(
        'interfaces.csv_scraper.CSVScraper.get_csv_data',
        lambda *args, **kwargs: (
            "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
            "2337545;317130;Test;20;MEDICO DA FAMILIA;202001"
        )
    )
    # stub error
    monkeypatch.setattr(
        'core.services.data_processor.DataProcessor.process_csv',
        lambda *args, **kwargs: (_ for _ in ()).throw(DataProcessingError('Proc error', {}))
    )
    data = {"cpf": "11111111111", "name": "Random Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is not None
    assert listener.error_event['status_code'] == 422


def test_sse_invalid_request_id(events_endpoint):
    r = requests.get(f"{events_endpoint}?request_id=invalid-id", stream=True, timeout=5)
    assert r.status_code == 200
    assert 'text/event-stream' in r.headers.get('Content-Type')
    r.close()


def test_invalid_csv_format(monkeypatch, process_endpoint, events_endpoint):
    monkeypatch.setattr(
        'interfaces.csv_scraper.CSVScraper.get_csv_data',
        lambda *args, **kwargs: 'invalid,format'
    )
    data = {"cpf": "11111111111", "name": "Random Professional"}
    resp = requests.post(process_endpoint, json=data, timeout=5)
    assert resp.status_code == 202
    req_id = resp.json()['request_id']

    listener = SSEListener(f"{events_endpoint}?request_id={req_id}")
    listener.start_listening()
    start = time.time()
    while time.time() - start < 5:
        if listener.error_event:
            break
        time.sleep(0.2)
    listener.stop_listening()

    assert listener.error_event is not None
    msg = listener.error_event['error'].lower()
    assert 'formato de dados inválido' in msg

# -------------- Non-existent endpoint --------------

def test_nonexistent_endpoint(test_server):
    r = requests.get(f"{BASE_URL}/no_such_route", timeout=5)
    assert r.status_code == 404
