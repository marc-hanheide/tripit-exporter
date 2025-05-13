"""
Tests for the TripIt MCP server functionality.
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from tripit_mcp.tripit_client import TripItAPIClient
from tripit_mcp.server import TripItService


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "TRIPIT_CONSUMER_KEY": "test_consumer_key",
        "TRIPIT_CONSUMER_SECRET": "test_consumer_secret",
        "TRIPIT_OAUTH_TOKEN": "test_oauth_token",
        "TRIPIT_OAUTH_TOKEN_SECRET": "test_oauth_token_secret"
    }):
        yield


@pytest.fixture
def mock_tripit_client():
    """Mock TripIt API client."""
    with patch("tripit_mcp.server.TripItAPIClient") as mock_client:
        client_instance = MagicMock()
        mock_client.return_value = client_instance
        yield client_instance


def test_tripit_service_init(mock_env_vars, mock_tripit_client):
    """Test TripItService initialization."""
    service = TripItService()
    
    assert service.consumer_key == "test_consumer_key"
    assert service.consumer_secret == "test_consumer_secret"
    assert service.oauth_token == "test_oauth_token"
    assert service.oauth_token_secret == "test_oauth_token_secret"
    
    assert mock_tripit_client.list_trips.called == False
    assert mock_tripit_client.get_trip.called == False


def test_tripit_api_client_list_trips():
    """Test TripItAPIClient list_trips method."""
    with patch.object(TripItAPIClient, "_make_request") as mock_request:
        # Mock the API response
        mock_request.return_value = {
            "Trip": [
                {
                    "id": "12345",
                    "display_name": "Test Trip",
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-07",
                    "primary_location": "Test Location",
                    "is_private": "false"
                }
            ]
        }
        
        client = TripItAPIClient("key", "secret")
        trips = client.list_trips(start_date="2023-01-01", end_date="2023-01-31")
        
        assert len(trips) == 1
        assert trips[0]["id"] == "12345"
        assert trips[0]["display_name"] == "Test Trip"
        
        mock_request.assert_called_once_with(
            "GET",
            "list/trip",
            params={
                "format": "json",
                "include_objects": "true",
                "start_date": "2023-01-01", 
                "end_date": "2023-01-31"
            }
        )


def test_tripit_api_client_get_trip():
    """Test TripItAPIClient get_trip method."""
    with patch.object(TripItAPIClient, "_make_request") as mock_request:
        # Mock the API response
        mock_request.return_value = {
            "Trip": {
                "id": "12345",
                "display_name": "Test Trip",
                "start_date": "2023-01-01",
                "end_date": "2023-01-07"
            }
        }
        
        client = TripItAPIClient("key", "secret")
        trip = client.get_trip(trip_id="12345")
        
        assert trip["id"] == "12345"
        assert trip["display_name"] == "Test Trip"
        
        mock_request.assert_called_once_with(
            "GET",
            "get/trip",
            params={
                "format": "json",
                "id": "12345",
                "include_objects": "true"
            }
        )
