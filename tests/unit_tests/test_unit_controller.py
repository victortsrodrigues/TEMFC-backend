import json
import pytest

from unittest.mock import patch, MagicMock

from controllers.controller import app

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@patch("controllers.controller.Services.run_services", return_value=50)
@patch("controllers.controller.ValidateSchema")
def test_process_data_success(mock_validate_schema, mock_run_services, client):
    # Set up the dummy validated data with the required attributes
    dummy_validated = MagicMock()
    dummy_validated.cpf = "12345678900"
    dummy_validated.name = "Fulano Cicrano"
    mock_validate_schema.return_value = dummy_validated

    # Prepare the JSON payload
    data = {"cpf": "12345678900", "name": "Fulano Cicrano"}

    # Send the POST request to the process_data endpoint
    response = client.post("/", json=data)
    response_data = response.get_json()

    # Validate the response
    assert response.status_code == 200
    assert response_data["name"] == "Fulano Cicrano"
    assert response_data["valid_months"] == 50
    assert response_data["status"] == "ELIGIBLE"
    assert response_data["pending_months"] == 0


@patch("controllers.controller.services.run_services", return_value=30)
@patch("controllers.controller.ValidateSchema")
def test_not_eligible(mock_validate_schema, mock_run_services):
    dummy_validated = MagicMock()
    dummy_validated.cpf = "12345678900"
    dummy_validated.name = "Fulano Cicrano"
    mock_validate_schema.return_value = dummy_validated

    client = app.test_client()
    data = {"cpf": "12345678900", "name": "Fulano Cicrano"}
    response = client.post("/", json=data)
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["name"] == "Fulano Cicrano"
    assert response_data["valid_months"] == 30
    assert response_data["status"] == "NOT ELIGIBLE"
    assert response_data["pending_months"] == 18
    assert "details" not in response_data
    
    
@patch("controllers.controller.services.get_result_details")
@patch("controllers.controller.services.run_services", return_value=50)
@patch("controllers.controller.ValidateSchema")
def test_eligible_with_details(mock_validate_schema, mock_run_services, mock_get_result_details):
    dummy_validated = MagicMock()
    dummy_validated.cpf = "12345678900"
    dummy_validated.name = "Fulano Cicrano"
    mock_validate_schema.return_value = dummy_validated

    # Simulate service details for the given name
    mock_get_result_details.return_value = {
        "Fulano Cicrano": {
            "semesters_40": 2,
            "semesters_30": 1,
            "semesters_20": 0
        }
    }

    client = app.test_client()
    data = {"cpf": "12345678900", "name": "Fulano Cicrano"}
    response = client.post("/", json=data)
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["name"] == "Fulano Cicrano"
    assert response_data["valid_months"] == 50
    assert response_data["status"] == "ELIGIBLE"
    assert response_data["pending_months"] == 0
    assert "details" in response_data
    details = response_data["details"]
    assert details["semesters_40"] == 2
    assert details["semesters_30"] == 1
    assert details["semesters_20"] == 0
        

@patch("controllers.controller.ValidateSchema", side_effect=Exception("Dummy validation error"))
def test_validation_error(mock_validate_schema, client):
    data = {"cpf": "bad-cpf", "name": "Bad Name"}
    
    response = client.post("/", json=data)
    response_data = response.get_json()
    
    assert response.status_code == 500
    assert "Processing failed" in response_data["error"]

    
@patch("controllers.controller.services.run_services", side_effect=Exception("Unexpected failure"))
@patch("controllers.controller.ValidateSchema")
def test_unexpected_exception(mock_validate_schema, mock_run_services):
    dummy_validated = MagicMock()
    dummy_validated.cpf = "12345678900"
    dummy_validated.name = "Fulano Cicrano"
    mock_validate_schema.return_value = dummy_validated

    client = app.test_client()
    data = {"cpf": "12345678900", "name": "Fulano Cicrano"}
    response = client.post("/", json=data)
    response_data = response.get_json()
    
    assert response.status_code == 500
    assert "Processing failed" in response_data["error"]
    

def test_pydantic_error(client):
    data = {"cpf": "bad-cpf", "name": "Bad Name"}
    
    response = client.post("/", json=data)
    response_data = response.get_json()
    
    assert response.status_code == 400
    assert "Invalid body" in response_data["error"]