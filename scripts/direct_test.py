#!/usr/bin/env python
"""
TripIt API Direct Test

This script makes a direct HTTP request to the TripIt API using the most 
basic possible approach to diagnose potential issues with connectivity or credentials.
"""

import os
import sys
import base64
import hashlib
import hmac
import random
import string
import time
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("This script requires the requests library.")
    print("Install with: pip install requests")
    sys.exit(1)


def run_test():
    """Run a direct test against the TripIt API."""
    print("TripIt Direct API Test")
    print("=====================")
    
    # Get credentials from environment
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        print("Error: Missing TripIt credentials")
        print("Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET environment variables")
        sys.exit(1)
    
    print(f"Using consumer key: {consumer_key}")
    print(f"Using consumer secret: {consumer_secret[:5]}...{consumer_secret[-5:]}")
    
    # Basic API test URL (public method that doesn't require authentication)
    test_url = "https://api.tripit.com/v1/ping"
    
    # Try direct API call without OAuth first
    print("\nTesting basic API connectivity...")
    try:
        response = requests.get(test_url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Now try with OAuth
    print("\nTesting OAuth request...")
    
    # 1. Generate OAuth params
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    timestamp = str(int(time.time()))
    
    request_token_url = "https://api.tripit.com/oauth/request_token"
    
    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_version': '1.0',
        'oauth_callback': 'oob',
    }
    
    # 2. Generate signature
    param_pairs = sorted((quote(k, safe=''), quote(v, safe='')) for k, v in oauth_params.items())
    param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
    base_string = f"GET&{quote(request_token_url, safe='')}&{quote(param_string, safe='')}"
    
    key = f"{quote(consumer_secret, safe='')}&"
    signature = base64.b64encode(
        hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    oauth_params['oauth_signature'] = signature
    
    # 3. Create auth header
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(oauth_params.items())
    )
    
    print(f"Authorization header: {auth_header}")
    
    # 4. Make the request
    headers = {
        'Authorization': auth_header,
        'User-Agent': 'TripIt-API-Test/1.0',
    }
    
    params = {'oauth_callback': 'oob'}  # Also include in query string
    
    try:
        response = requests.get(request_token_url, headers=headers, params=params)
        print(f"\nStatus: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: '{response.text}'")
        
        # Try alternative URL format
        alt_url = "https://api.tripit.com/oauth/request_token?oauth_callback=oob"
        print("\nTrying alternative URL format...")
        response = requests.get(alt_url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: '{response.text}'")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    run_test()
