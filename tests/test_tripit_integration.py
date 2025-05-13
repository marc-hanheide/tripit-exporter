"""
Integration tests for TripIt MCP using actual API credentials.
This test requires real TripIt API credentials to be set in the environment.
"""

import os
import sys
import pytest
from unittest import skipIf

from tripit_mcp.tripit_client import TripItAPIClient


def has_required_credentials():
    """Check if the required TripIt API credentials are available."""
    consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY")
    consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET")
    return bool(consumer_key and consumer_secret and consumer_key != "your_consumer_key_here" and consumer_secret != "your_consumer_secret_here")


@skipIf(not has_required_credentials(), "TripIt API credentials not set in environment")
class TestTripItIntegration:
    """Integration tests for TripIt MCP using actual API credentials."""

    def setup_method(self):
        """Set up the test environment."""
        self.consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET")
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN")
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET")
        
        # Initialize the client with actual credentials
        self.client = TripItAPIClient(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            oauth_token=self.oauth_token if self.oauth_token and self.oauth_token.strip() else None,
            oauth_token_secret=self.oauth_token_secret if self.oauth_token_secret and self.oauth_token_secret.strip() else None
        )

    def test_list_trips(self):
        """Test listing trips using actual API credentials."""
        print("\nFetching trips from TripIt API...")
        try:
            # Try to fetch trips for the next year
            trips = self.client.list_trips(start_date="2025-01-01", end_date="2026-01-01")
            
            # Basic validation of the response
            assert isinstance(trips, list), "Expected trips to be a list"
            print(f"Successfully fetched {len(trips)} trips")
            
            # Print details of each trip for verification
            for i, trip in enumerate(trips[:5]):  # Limit to 5 trips to avoid too much output
                print(f"Trip {i+1}: {trip.get('display_name', 'Unnamed')} - {trip.get('start_date')} to {trip.get('end_date')}")
                
            # If we have trips, test the get_trip endpoint with the first trip ID
            if trips:
                first_trip_id = trips[0]['id']
                print(f"\nFetching details for trip ID: {first_trip_id}")
                trip_details = self.client.get_trip(first_trip_id)
                assert trip_details['id'] == first_trip_id
                print(f"Successfully fetched details for: {trip_details.get('display_name')}")
                
        except Exception as e:
            # Print the exception but don't fail the test if there's a valid connection issue
            print(f"Error fetching trips: {str(e)}")
            pytest.fail(f"API test failed: {str(e)}")


if __name__ == "__main__":
    # Allow running this test file directly
    if has_required_credentials():
        test = TestTripItIntegration()
        test.setup_method()
        test.test_list_trips()
    else:
        print("ERROR: TripIt API credentials not set in environment")
        print("Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET environment variables")
        sys.exit(1)
