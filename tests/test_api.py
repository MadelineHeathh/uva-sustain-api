"""
Smoke tests for UVA Sustainability Metrics API
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from app import app, load_data


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def setup_data():
    """Load test data."""
    load_data()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'service' in data


def test_list_buildings(client, setup_data):
    """Test listing all buildings."""
    response = client.get('/api/v1/buildings')
    assert response.status_code == 200
    data = response.get_json()
    assert 'buildings' in data
    assert 'count' in data
    assert isinstance(data['buildings'], list)


def test_get_all_metrics(client, setup_data):
    """Test getting all metrics."""
    response = client.get('/api/v1/metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert 'count' in data
    assert isinstance(data['data'], list)


def test_get_metrics_by_building(client, setup_data):
    """Test filtering metrics by building."""
    response = client.get('/api/v1/metrics?building=Alderman')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert len(data['data']) > 0


def test_get_specific_building(client, setup_data):
    """Test getting metrics for a specific building."""
    response = client.get('/api/v1/metrics/Alderman%20Library')
    assert response.status_code == 200
    data = response.get_json()
    assert 'building' in data
    assert 'data' in data


def test_get_campus_wide_metrics(client, setup_data):
    """Test getting campus-wide aggregated metrics."""
    response = client.get('/api/v1/metrics/campus-wide')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert 'aggregation' in data


def test_get_campus_wide_by_year(client, setup_data):
    """Test getting campus-wide metrics filtered by year."""
    response = client.get('/api/v1/metrics/campus-wide?year=2022')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data


def test_invalid_building(client, setup_data):
    """Test handling of non-existent building."""
    response = client.get('/api/v1/metrics/NonExistentBuilding')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

