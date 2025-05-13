#!/usr/bin/env python
"""
Example script demonstrating OAuth authentication with the TripIt API.

This script demonstrates the complete OAuth flow for TripIt API:
1. Getting a request token
2. Authorizing the application
3. Exchanging for an access token
4. Making authenticated API calls

Usage:
  python auth_example.py

Environment Variables:
  TRIPIT_CONSUMER_KEY - Your TripIt API consumer key
  TRIPIT_CONSUMER_SECRET - Your TripIt API consumer secret
"""

import os
import sys
from datetime import datetime, timedelta

from tripit_mcp.oauth import TripItOAuth
from tripit_mcp.tripit_client import TripItAPIClient

# Get API credentials from environment
consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')

if not consumer_key or not consumer_secret:
    print("Error: TripIt API credentials not found in environment variables.")
    print("Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET.")
    sys.exit(1)

print("TripIt API OAuth Authentication Example")
print("======================================")

# Step 1: Initialize OAuth handler
oauth = TripItOAuth(consumer_key, consumer_secret)

# Step 2: Go through OAuth flow and get access tokens
try:
    access_token, access_token_secret = oauth.authorize_app()
except Exception as e:
    print(f"Authentication failed: {str(e)}")
    sys.exit(1)

print("\nTesting authenticated API access...")

# Step 3: Use the tokens to initialize a TripIt client
client = TripItAPIClient(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    oauth_token=access_token,
    oauth_token_secret=access_token_secret
)

# Step 4: Make an authenticated API call
try:
    # Calculate date range for the next year
    today = datetime.now()
    next_year = today + timedelta(days=365)
    
    # Format dates as YYYY-MM-DD
    start_date = today.strftime("%Y-%m-%d")
    end_date = next_year.strftime("%Y-%m-%d")
    
    # Fetch trips for the next year
    print(f"\nFetching trips from {start_date} to {end_date}...")
    trips = client.list_trips(start_date=start_date, end_date=end_date)
    
    print(f"Successfully retrieved {len(trips)} trips:")
    for i, trip in enumerate(trips[:5]):  # Show up to 5 trips
        print(f"{i+1}. {trip.get('display_name')}: {trip.get('start_date')} to {trip.get('end_date')}")
    
    if len(trips) > 5:
        print(f"...and {len(trips) - 5} more")
        
    print("\nAuthentication and API access test successful!")
except Exception as e:
    print(f"API call failed: {str(e)}")
    sys.exit(1)
