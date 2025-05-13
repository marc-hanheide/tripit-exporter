#!/usr/bin/env python
"""
Alternative TripIt OAuth implementation using the requests library.

This script provides a direct implementation of the TripIt OAuth process
using the requests library instead of httpx to help diagnose any library-specific issues.

Run this script to test TripIt API OAuth authentication directly.
"""

import base64
import hashlib
import hmac
import os
import random
import string
import sys
import time
import webbrowser
from urllib.parse import parse_qsl, quote, urlencode

try:
    import requests
except ImportError:
    print("This script requires the requests library.")
    print("Please install it with: pip install requests")
    sys.exit(1)


# TripIt OAuth endpoints
REQUEST_TOKEN_URL = "https://api.tripit.com/oauth/request_token"
AUTHORIZE_URL = "https://www.tripit.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.tripit.com/oauth/access_token"


def get_tripit_credentials():
    """Get TripIt API credentials from environment variables or prompt."""
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API consumer key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API consumer secret: ")
    
    if not consumer_key or not consumer_secret:
        print("Error: Both consumer key and consumer secret are required.")
        sys.exit(1)
    
    return consumer_key, consumer_secret


def generate_nonce(length=32):
    """Generate a random nonce."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def generate_signature(method, url, params, consumer_secret, token_secret=None):
    """Generate OAuth 1.0a signature."""
    # 1. Sort and encode parameters
    param_pairs = sorted((quote(k, safe=''), quote(v, safe='')) for k, v in params.items())
    param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
    
    # 2. Create base string
    base_string = f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"
    
    # 3. Create signing key
    key = f"{quote(consumer_secret, safe='')}&"
    if token_secret:
        key += quote(token_secret, safe='')
    
    # 4. Generate HMAC-SHA1 signature
    signature = base64.b64encode(
        hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    return signature


def get_request_token(consumer_key, consumer_secret):
    """Get a request token from TripIt."""
    # 1. Prepare OAuth parameters
    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': generate_nonce(),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
        'oauth_callback': 'oob',
    }
    
    # 2. Generate signature
    signature = generate_signature('GET', REQUEST_TOKEN_URL, oauth_params, consumer_secret)
    oauth_params['oauth_signature'] = signature
    
    # 3. Create Authorization header
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(oauth_params.items())
    )
    
    # 4. Print debug info
    print("\n==== Request Token Request ====")
    print(f"URL: {REQUEST_TOKEN_URL}")
    print(f"Authorization header: {auth_header}")
    
    # 5. Send request
    headers = {'Authorization': auth_header}
    params = {'oauth_callback': 'oob'}  # Explicitly include in query string as well
    
    try:
        response = requests.get(REQUEST_TOKEN_URL, headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: '{response.text}'")
        
        response.raise_for_status()
        
        # 6. Parse response
        if not response.text.strip():
            raise Exception("Empty response received from TripIt API")
            
        response_params = dict(parse_qsl(response.text))
        print(f"Parsed Response: {response_params}")
        
        # 7. Extract tokens
        if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
            raise Exception(f"Invalid response from TripIt API: {response.text}")
        
        return response_params['oauth_token'], response_params['oauth_token_secret']
    
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        sys.exit(1)


def get_user_authorization(token):
    """Direct user to TripIt authorization page and wait for confirmation."""
    auth_url = f"{AUTHORIZE_URL}?oauth_token={token}"
    print(f"\n==== User Authorization ====")
    print(f"Opening authorization URL: {auth_url}")
    webbrowser.open(auth_url)
    print("Please log in to TripIt (if necessary) and authorize the application.")
    input("Press Enter after you've completed the authorization...")


def get_access_token(consumer_key, consumer_secret, oauth_token, oauth_token_secret):
    """Exchange the request token for an access token."""
    # 1. Prepare OAuth parameters
    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_token': oauth_token,
        'oauth_nonce': generate_nonce(),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
    }
    
    # 2. Generate signature
    signature = generate_signature('GET', ACCESS_TOKEN_URL, oauth_params, 
                                  consumer_secret, oauth_token_secret)
    oauth_params['oauth_signature'] = signature
    
    # 3. Create Authorization header
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(oauth_params.items())
    )
    
    # 4. Print debug info
    print("\n==== Access Token Request ====")
    print(f"URL: {ACCESS_TOKEN_URL}")
    print(f"Authorization header: {auth_header}")
    
    # 5. Send request
    headers = {'Authorization': auth_header}
    
    try:
        response = requests.get(ACCESS_TOKEN_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: '{response.text}'")
        
        response.raise_for_status()
        
        # 6. Parse response
        if not response.text.strip():
            raise Exception("Empty response received from TripIt API")
            
        response_params = dict(parse_qsl(response.text))
        print(f"Parsed Response: {response_params}")
        
        # 7. Extract tokens
        if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
            raise Exception(f"Invalid response from TripIt API: {response.text}")
        
        return response_params['oauth_token'], response_params['oauth_token_secret']
    
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        sys.exit(1)


def main():
    """Run the TripIt OAuth flow."""
    print("TripIt OAuth Authentication - Alternative Implementation")
    print("=====================================================")
    
    # 1. Get credentials
    consumer_key, consumer_secret = get_tripit_credentials()
    print(f"Using Consumer Key: {consumer_key}")
    print(f"Using Consumer Secret: {consumer_secret[:5]}...{consumer_secret[-5:]}")
    
    try:
        # 2. Get request token
        print("\nStep 1: Getting request token...")
        oauth_token, oauth_token_secret = get_request_token(consumer_key, consumer_secret)
        print(f"Request Token: {oauth_token}")
        print(f"Request Token Secret: {oauth_token_secret}")
        
        # 3. Get user authorization
        print("\nStep 2: Getting user authorization...")
        get_user_authorization(oauth_token)
        
        # 4. Get access token
        print("\nStep 3: Getting access token...")
        access_token, access_token_secret = get_access_token(
            consumer_key, consumer_secret, oauth_token, oauth_token_secret
        )
        
        # 5. Show results
        print("\n==== OAuth Authorization Complete! ====")
        print("Your OAuth tokens have been successfully generated.")
        print("To use these tokens with the TripIt MCP Server, add them to your .env file:")
        print(f"\nTRIPIT_OAUTH_TOKEN={access_token}")
        print(f"TRIPIT_OAUTH_TOKEN_SECRET={access_token_secret}\n")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
