#!/usr/bin/env python
"""
TripIt OAuth Flow Example

This script demonstrates the complete OAuth 1.0a flow for the TripIt API:
1. Getting a request token
2. Getting user authorization
3. Exchanging for an access token
4. Making authenticated API calls

Usage:
    python oauth_flow.py

Environment variables:
    TRIPIT_CONSUMER_KEY - Your TripIt API consumer key
    TRIPIT_CONSUMER_SECRET - Your TripIt API consumer secret
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to PATH so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tripit_mcp.oauth import TripItOAuth
from tripit_mcp.tripit_client import TripItAPIClient, TripItAPIError


def demo_oauth_flow():
    """
    Demonstrate the complete OAuth flow with TripIt API.
    """
    print("TripIt OAuth Flow Example")
    print("=======================\n")
    
    # Step 0: Get API credentials
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API consumer key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API consumer secret: ")
    
    if not consumer_key or not consumer_secret:
        print("Error: Both consumer key and secret are required")
        sys.exit(1)
    
    # Step 1-3: Complete OAuth flow
    oauth = TripItOAuth(consumer_key, consumer_secret)
    
    try:
        # This will handle the complete OAuth flow and return tokens
        access_token, access_token_secret = oauth.authorize_app()
        
        # Step 4: Use the tokens to make API calls
        demo_api_calls(consumer_key, consumer_secret, access_token, access_token_secret)
        
    except Exception as e:
        print(f"Error during OAuth flow: {e}")
        sys.exit(1)


def demo_api_calls(consumer_key, consumer_secret, oauth_token, oauth_token_secret):
    """
    Demonstrate API calls using the obtained OAuth tokens.
    
    Args:
        consumer_key: TripIt API consumer key
        consumer_secret: TripIt API consumer secret
        oauth_token: OAuth access token
        oauth_token_secret: OAuth access token secret
    """
    print("\n--- Making API calls with OAuth tokens ---\n")
    
    try:
        # Create API client
        client = TripItAPIClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            oauth_token=oauth_token,
            oauth_token_secret=oauth_token_secret
        )
        
        # Example 1: List all trips
        print("Example 1: Listing all trips")
        trips = client.list_trips()
        print(f"Found {len(trips)} trip(s) in your TripIt account")
        
        # Example 2: List trips in a date range
        print("\nExample 2: Listing trips within a date range")
        today = datetime.now()
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=180)
        date_filtered_trips = client.list_trips(
            start_date=start_date.strftime("%Y-%m-%d"), 
            end_date=end_date.strftime("%Y-%m-%d")
        )
        print(f"Found {len(date_filtered_trips)} trip(s) between "
              f"{start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")
        
        # Show a sample of trips if any were found
        if trips:
            print("\nSample trip information:")
            trip = trips[0]
            print(f"  Trip: {trip.get('display_name', 'Unnamed Trip')}")
            print(f"  ID: {trip.get('id', 'Unknown')}")
            print(f"  Dates: {trip.get('start_date', 'Unknown')} - {trip.get('end_date', 'Unknown')}")
            print(f"  Primary Location: {trip.get('primary_location', 'Unknown')}")
            
            # Example 3: Get details for a specific trip
            if trip.get('id'):
                print(f"\nExample 3: Getting details for trip {trip['id']}")
                try:
                    trip_details = client.get_trip(trip['id'])
                    print("Successfully retrieved trip details")
                    
                    # Show some of the trip objects if available
                    if 'TripInvitees' in trip_details:
                        print(f"  Trip has {len(trip_details['TripInvitees'])} invitees")
                    
                    if 'Segments' in trip_details:
                        print(f"  Trip has {len(trip_details['Segments'])} segments")
                        for i, segment in enumerate(trip_details['Segments'], 1):
                            seg_type = segment.get('segment_type_code', 'Unknown')
                            print(f"    Segment {i}: {seg_type}")
                except Exception as e:
                    print(f"Error getting trip details: {e}")
        else:
            print("\nNo trips found to show details for")
        
        print("\nAPI calls completed successfully!")
        print("Your OAuth tokens are working correctly.")
        print(f"\nOAuth Token: {oauth_token}")
        print(f"OAuth Token Secret: {oauth_token_secret}")
        print("\nAdd these to your .env file to use with the TripIt MCP Server.")
        
    except TripItAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    demo_oauth_flow()
