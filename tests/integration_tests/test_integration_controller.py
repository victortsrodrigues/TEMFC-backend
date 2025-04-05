import json
import pytest
import math

from src.controllers.controller import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestControllerRealIntegration:
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    

    def test_process_data_not_eligible(self, client):
        """
        Test the full integration of the API with real service implementation
        using the specified CPF and name, with in-memory CSV data.
        """
        
        # Test data
        test_data = {
            "cpf": "05713248356",
            "name": "Leticia Lima Luz"
        }
        
        # Make the API request
        response = client.post(
            '/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode('utf-8')}")
        
        # Assertions
        assert response.status_code == 200
        
        # Parse the response data
        data = json.loads(response.data)
        
        # Verify the structure of the response
        assert 'name' in data
        assert 'valid_months' in data
        assert 'status' in data
        assert 'pending_months' in data
              
        assert data['valid_months'] == 2
        assert data['status'] == 'NOT ELIGIBLE'
        assert data['pending_months'] == 46
        
        # If details are provided, verify them
        if 'details' in data:
            assert 'semesters_40' in data['details']
            assert 'semesters_30' in data['details']
            assert 'semesters_20' in data['details']
            
            assert data['details']['semesters_40'] == 0
            assert data['details']['semesters_30'] == 0
            assert data['details']['semesters_20'] == 0
        

    def test_process_data_eligible(self, client):
        """
        Test the full integration of the API with real service implementation
        using the specified CPF and name, with in-memory CSV data.
        """
        
        # Test data
        test_data = {
            "cpf": "01237925177",
            "name": "Laís Lena Pereira Silva"
        }
        
        # Make the API request
        response = client.post(
            '/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode('utf-8')}")
        
        # Assertions
        assert response.status_code == 200
        
        # Parse the response data
        data = json.loads(response.data)
        
        # Verify the structure of the response
        assert 'name' in data
        assert 'valid_months' in data
        assert 'status' in data
        assert 'pending_months' in data
              
        assert math.isclose(data['valid_months'], 53.25)
        assert data['status'] == 'ELIGIBLE'
        assert data['pending_months'] == 0
        
        # If details are provided, verify them
        if 'details' in data:
            assert 'semesters_40' in data['details']
            assert 'semesters_30' in data['details']
            assert 'semesters_20' in data['details']
            
            assert data['details']['semesters_40'] == 7
            assert data['details']['semesters_30'] == 2
            assert data['details']['semesters_20'] == 0

    
    def test_process_data_validation_error(self, client):
        """Test validation error handling"""
        # Test data with missing required fields
        test_data = {
            "cpf": "12345678900"
            # Missing 'name' field
        }
        
        # Make request
        response = client.post(
            '/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Assertions
        assert response.status_code == 400  # Bad request
        data = json.loads(response.data)
        assert 'error' in data
        assert 'details' in data
        
        
    def test_http_exception_handler(self, client):
        """Test HTTP exception handling"""
        # Make request to non-existent endpoint
        response = client.get('/non-existent-endpoint')
        
        # Assertions
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['status_code'] == 404
        
        
    def test_not_found_csv_data(self, client):
        test_data = {
            "cpf": "12345678910",
            "name": "Fulano Cicrano"
        }
        
        response = client.post(
            '/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Assertions
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'details' in data