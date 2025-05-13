#!/usr/bin/env python
"""
Minimal TripIt OAuth Implementation - OAuth 1.0a

This is a bare-bones implementation using only the standard library
to help isolate potential issues with OAuth authentication.
"""

import base64
import hashlib
import hmac
import os
import random
import string
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

# TripIt API endpoints
REQUEST_TOKEN_URL = "https://api.tripit.com/oauth/request_token"
AUTHORIZE_URL = "https://www.tripit.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.tripit.com/oauth/access_token"

def get_credentials():
    """Get TripIt API credentials from environment variables or user input."""
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API consumer key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API consumer secret: ")
    
    return consumer_key, consumer_secret

def generate_nonce(length=32):
    """Generate a random nonce."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def make_oauth_request(url, consumer_key, consumer_secret, 
                      oauth_token=None, oauth_token_secret=None, method="GET",
                      additional_params=None):
    """
    Make an OAuth 1.0a request with minimal dependencies.
    
    Returns:
        The response text
    """
    print(f"\nMaking OAuth request to: {url}")
    
    # 1. Create OAuth parameters
    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': generate_nonce(),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
    }
    
    # Add token if provided
    if oauth_token:
        oauth_params['oauth_token'] = oauth_token
        
    # Add additional parameters if provided
    if additional_params:
        for key, value in additional_params.items():
            oauth_params[key] = value
    
    # 2. Create signature
    # Sort and encode parameters
    all_params = {**oauth_params}
    param_pairs = sorted((urllib.parse.quote(str(k), safe=''), 
                          urllib.parse.quote(str(v), safe='')) 
                        for k, v in all_params.items())
    param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
    
    # Create base string
    base_string = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
    print(f"Base string: {base_string}")
    
    # Create signing key
    signing_key = f"{urllib.parse.quote(consumer_secret, safe='')}&"
    if oauth_token_secret:
        signing_key += urllib.parse.quote(oauth_token_secret, safe='')
    print(f"Signing key: {signing_key}")
    
    # Generate signature
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    # Add signature to parameters
    oauth_params['oauth_signature'] = signature
    
    # 3. Create Authorization header
    auth_header = 'OAuth ' + ', '.join(
        f'{urllib.parse.quote(str(k), safe="")}="{urllib.parse.quote(str(v), safe="~")}"' 
        for k, v in sorted(oauth_params.items())
    )
    print(f"Authorization header: {auth_header}")
    
    # 4. Make the request
    if additional_params and any(k not in oauth_params for k in additional_params):
        query_params = '&'.join(f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" 
                               for k, v in additional_params.items() 
                               if k not in oauth_params)
        if '?' in url:
            url = f"{url}&{query_params}"
        else:
            url = f"{url}?{query_params}"
    
    # Create request
    req = urllib.request.Request(url)
    req.add_header('Authorization', auth_header)
    req.add_header('User-Agent', 'TripIt-Minimal-OAuth/1.0')
    
    try:
        # Send request
        print(f"Sending request to {url}")
        with urllib.request.urlopen(req) as response:
            response_text = response.read().decode('utf-8')
            print(f"Response status: {response.getcode()}")
            print(f"Response text: {response_text}")
            return response_text
    except urllib.error.HTTPError as e:
        error_text = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print(f"Error {e.code}: {error_text}")
        raise
    except urllib.error.URLError as e:
        print(f"URL Error: {str(e)}")
        raise

def parse_response_params(response_text):
    """Parse OAuth response parameters."""
    return dict(urllib.parse.parse_qsl(response_text))

def verify_tripit_api_access(consumer_key, consumer_secret):
    """Test if the TripIt API is accessible with these credentials."""
    print("\nVerifying TripIt API access...")
    try:
        # Try to access a public API endpoint
        url = "https://api.tripit.com/v1/ping"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'TripIt-Test/1.0')
        
        with urllib.request.urlopen(req) as response:
            print(f"TripIt API is accessible. Status: {response.getcode()}")
            if response.getcode() == 200:
                print("Basic API connectivity confirmed.")
                return True
    except Exception as e:
        print(f"Error accessing TripIt API: {str(e)}")
        print("There may be network connectivity issues or the API might be down.")
        return False

def main():
    """Run the minimal TripIt OAuth flow."""
    print("TripIt OAuth Authentication - Minimal Implementation")
    print("=================================================")
    
    try:
        # Get TripIt API credentials
        consumer_key, consumer_secret = get_credentials()
        print(f"Using Consumer Key: {consumer_key}")

        # Test basic API access first
        if not verify_tripit_api_access(consumer_key, consumer_secret):
            print("WARNING: Basic TripIt API access test failed, but continuing with OAuth...")
        
        print("\n=== STEP 1: Getting Request Token ===")
        
        # Include oauth_callback in the additional params
        additional_params = {'oauth_callback': 'oob'}
        
        # Make request token request
        response_text = make_oauth_request(
            url=REQUEST_TOKEN_URL,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            additional_params=additional_params
        )
        
        # Parse response
        response_params = parse_response_params(response_text)
        
        # Check if we got a valid response
        if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
            print("Error: Invalid response from request_token endpoint")
            sys.exit(1)
        
        request_token = response_params['oauth_token']
        request_token_secret = response_params['oauth_token_secret']
        
        print(f"Request Token: {request_token}")
        print(f"Request Token Secret: {request_token_secret}")
        
        # Build authorization URL
        auth_url = f"{AUTHORIZE_URL}?oauth_token={urllib.parse.quote(request_token)}"
        
        print("\n=== STEP 2: User Authorization ===")
        print(f"Opening browser to: {auth_url}")
        print("Please log in to TripIt (if necessary) and authorize the application")
        
        # Open browser for authorization
        webbrowser.open(auth_url)
        
        # Wait for user confirmation
        input("Press Enter after you've authorized the application...")
        
        print("\n=== STEP 3: Getting Access Token ===")
        
        # Make access token request
        response_text = make_oauth_request(
            url=ACCESS_TOKEN_URL,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            oauth_token=request_token,
            oauth_token_secret=request_token_secret
        )
        
        # Parse response
        response_params = parse_response_params(response_text)
        
        # Check if we got a valid response
        if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
            print("Error: Invalid response from access_token endpoint")
            sys.exit(1)
        
        access_token = response_params['oauth_token']
        access_token_secret = response_params['oauth_token_secret']
        
        print("\n=== OAuth Authentication Successful! ===")
        print("Access Token:", access_token)
        print("Access Token Secret:", access_token_secret)
        print("\nAdd these to your .env file:")
        print(f"TRIPIT_OAUTH_TOKEN={access_token}")
        print(f"TRIPIT_OAUTH_TOKEN_SECRET={access_token_secret}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
