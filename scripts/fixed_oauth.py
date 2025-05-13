#!/usr/bin/env python
"""
Fixed TripIt OAuth Implementation

This script implements the TripIt OAuth 1.0a flow with strict adherence to
the OAuth 1.0a specification and TripIt's specific requirements.

Key corrections:
1. Proper parameter encoding (RFC 3986)
2. Strict ordering of parameters for signature base string
3. Proper OAuth callback handling
4. Detailed error reporting
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
    from requests.auth import AuthBase
except ImportError:
    print("This script requires the requests library.")
    print("Please install it with: pip install requests")
    sys.exit(1)


# TripIt OAuth endpoints
REQUEST_TOKEN_URL = "https://api.tripit.com/oauth/request_token"
AUTHORIZE_URL = "https://www.tripit.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.tripit.com/oauth/access_token"


class TripItOAuthSigner(AuthBase):
    """OAuth 1.0a signer for TripIt API requests"""
    
    def __init__(self, consumer_key, consumer_secret, oauth_token=None, oauth_token_secret=None, callback='oob'):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.callback = callback
    
    def __call__(self, r):
        """Sign the request with OAuth 1.0a"""
        # Parse URL to get base URL (without query parameters)
        url_parts = r.url.split('?', 1)
        base_url = url_parts[0]
        
        # Get parameters from URL if any
        query_params = {}
        if len(url_parts) > 1:
            query_params = dict(parse_qsl(url_parts[1]))
        
        # Create OAuth parameters
        oauth_params = self._get_oauth_params()
        
        # Add parameters from URL to OAuth parameters for signature
        all_params = {**oauth_params, **query_params}
        
        # Generate signature
        oauth_params['oauth_signature'] = self._generate_signature(r.method, base_url, all_params)
        
        # Set the Authorization header
        r.headers['Authorization'] = self._get_oauth_header(oauth_params)
        
        # For debugging - log the complete request
        debug_output = f"\nFinal Request:\nMethod: {r.method}\nURL: {r.url}\nHeaders: {r.headers}\n"
        print(debug_output)
        
        return r
    
    def _get_oauth_params(self):
        """Create base OAuth parameters"""
        params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
        }
        
        # Add token if available
        if self.oauth_token:
            params['oauth_token'] = self.oauth_token
            
        # Add callback for request token only if token is not yet available
        if not self.oauth_token and self.callback:
            params['oauth_callback'] = self.callback
            
        return params
    
    def _generate_nonce(self, length=32):
        """Generate a random nonce"""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def _generate_signature(self, method, url, params):
        """Generate OAuth 1.0a signature"""
        # 1. Create parameter string - MUST use RFC 3986 encoding
        param_pairs = []
        for k, v in sorted(params.items()):
            # Encode key and value separately per RFC 3986
            k_enc = quote(str(k), safe='')
            v_enc = quote(str(v), safe='')
            param_pairs.append(f"{k_enc}={v_enc}")
        
        param_string = '&'.join(param_pairs)
        
        # 2. Create signature base string
        base_string_parts = [
            method.upper(),
            quote(url, safe=''),
            quote(param_string, safe='')
        ]
        base_string = '&'.join(base_string_parts)
        
        # 3. Create signing key
        key_parts = [
            quote(self.consumer_secret, safe=''),
            quote(self.oauth_token_secret if self.oauth_token_secret else '', safe='')
        ]
        key = '&'.join(key_parts)
        
        # 4. Generate HMAC-SHA1 signature
        signature = base64.b64encode(
            hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature
    
    def _get_oauth_header(self, oauth_params):
        """Create the OAuth Authorization header"""
        auth_header_parts = []
        for k, v in sorted(oauth_params.items()):
            auth_header_parts.append(f'{quote(k, safe="")}="{quote(v, safe="~")}"')
        
        return 'OAuth ' + ', '.join(auth_header_parts)


def get_request_token(consumer_key, consumer_secret):
    """Get a request token from TripIt."""
    print("\nStep 1: Getting request token from TripIt...")
    
    auth = TripItOAuthSigner(consumer_key, consumer_secret, callback='oob')
    
    try:
        # Make the request with explicit callback both in OAuth parameters and query
        params = {'oauth_callback': 'oob'}
        response = requests.get(REQUEST_TOKEN_URL, params=params, auth=auth)
        
        # Print response details
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: '{response.text}'")
        
        # Check for errors
        response.raise_for_status()
        
        # Parse response
        if not response.text.strip():
            raise ValueError("Empty response received from TripIt API")
        
        token_data = dict(parse_qsl(response.text))
        
        # Verify token was received
        if 'oauth_token' not in token_data or 'oauth_token_secret' not in token_data:
            raise ValueError(f"Invalid token response: {response.text}")
            
        print(f"Successfully obtained request token: {token_data['oauth_token']}")
        return token_data['oauth_token'], token_data['oauth_token_secret']
        
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Error details: {e.response.status_code} - {e.response.text}")
        sys.exit(1)


def get_user_authorization(token):
    """Direct the user to authorize the request token."""
    auth_url = f"{AUTHORIZE_URL}?oauth_token={token}&oauth_callback=oob"
    print(f"\nStep 2: Please authorize this application...")
    print(f"Opening browser to: {auth_url}")
    
    # Open the browser for the user
    webbrowser.open(auth_url)
    
    # Wait for user confirmation
    input("\nPress Enter after you've authorized the application in your browser...\n")


def get_access_token(consumer_key, consumer_secret, oauth_token, oauth_token_secret):
    """Exchange the authorized request token for an access token."""
    print("\nStep 3: Getting access token from TripIt...")
    
    auth = TripItOAuthSigner(
        consumer_key, consumer_secret, 
        oauth_token=oauth_token, 
        oauth_token_secret=oauth_token_secret
    )
    
    try:
        # Make the request
        response = requests.get(ACCESS_TOKEN_URL, auth=auth)
        
        # Print response details
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: '{response.text}'")
        
        # Check for errors
        response.raise_for_status()
        
        # Parse response
        token_data = dict(parse_qsl(response.text))
        
        # Verify token was received
        if 'oauth_token' not in token_data or 'oauth_token_secret' not in token_data:
            raise ValueError(f"Invalid token response: {response.text}")
            
        print(f"Successfully obtained access token: {token_data['oauth_token']}")
        return token_data['oauth_token'], token_data['oauth_token_secret']
        
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Error details: {e.response.status_code} - {e.response.text}")
        sys.exit(1)


def verify_api_access():
    """Verify basic connectivity to the TripIt API."""
    print("\nVerifying TripIt API connectivity...")
    try:
        response = requests.get("https://api.tripit.com/v1/ping")
        print(f"TripIt API is accessible. Status: {response.status_code}")
        if response.status_code == 200:
            return True
        return False
    except:
        print("Warning: Unable to connect to TripIt API")
        return False


def test_api_call(consumer_key, consumer_secret, oauth_token, oauth_token_secret):
    """Test API call with the generated access token"""
    print("\nTesting API access with obtained tokens...")
    
    api_url = "https://api.tripit.com/v1/list/trip/format/json"
    
    auth = TripItOAuthSigner(
        consumer_key, consumer_secret, 
        oauth_token=oauth_token, 
        oauth_token_secret=oauth_token_secret
    )
    
    try:
        response = requests.get(api_url, auth=auth)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("API call successful! Your OAuth tokens are working correctly.")
            data = response.json()
            if 'Trip' in data:
                trips = data['Trip']
                if isinstance(trips, list):
                    print(f"Found {len(trips)} trips in your account.")
                else:
                    print(f"Found 1 trip in your account.")
            else:
                print("No trips found in your account (or empty response).")
        else:
            print(f"API call failed: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {str(e)}")


def main():
    """Execute the OAuth flow."""
    print("TripIt OAuth Authorization - Fixed Implementation")
    print("==============================================")
    
    # Get credentials from environment or prompt
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API consumer key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API consumer secret: ")
    
    if not consumer_key or not consumer_secret:
        print("Error: Both consumer key and consumer secret are required.")
        sys.exit(1)
        
    print(f"Using Consumer Key: {consumer_key}")
    print(f"Using Consumer Secret: {consumer_secret[:5]}...{consumer_secret[-5:] if len(consumer_secret) > 10 else '***'}")
    
    # Verify API connectivity 
    verify_api_access()
    
    try:
        # Execute OAuth flow
        request_token, request_token_secret = get_request_token(consumer_key, consumer_secret)
        get_user_authorization(request_token)
        access_token, access_token_secret = get_access_token(consumer_key, consumer_secret, request_token, request_token_secret)
        
        # Display the results
        print("\n==== OAuth Authorization Complete! ====")
        print("Your OAuth tokens have been successfully generated.")
        print("Add these to your .env file:")
        print(f"\nTRIPIT_OAUTH_TOKEN={access_token}")
        print(f"TRIPIT_OAUTH_TOKEN_SECRET={access_token_secret}\n")
        
        # Test the tokens
        should_test = input("Would you like to test the generated tokens? (y/n): ").lower()
        if should_test == 'y':
            test_api_call(consumer_key, consumer_secret, access_token, access_token_secret)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
