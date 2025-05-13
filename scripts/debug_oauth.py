#!/usr/bin/env python
"""
TripIt OAuth Debug Tool - Test the OAuth process with full diagnostic output

This script helps diagnose TripIt OAuth authentication issues by:
1. Making OAuth request token calls with detailed logging
2. Verifying header and signature formats
3. Printing all request and response details

Usage:
  python debug_oauth.py

Environment Variables:
  TRIPIT_CONSUMER_KEY - Your TripIt API consumer key
  TRIPIT_CONSUMER_SECRET - Your TripIt API consumer secret
"""

import base64
import hashlib
import hmac
import os
import random
import string
import sys
import time
from urllib.parse import quote, parse_qsl

import httpx


def debug_tripit_oauth():
    """Debug TripIt OAuth process with detailed logging."""
    print("\n===== TripIt OAuth Debug Tool =====\n")
    
    # Get credentials from environment or prompt
    consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY")
    consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET")
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API Consumer Key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API Consumer Secret: ")
    
    if not consumer_key or not consumer_secret:
        print("Error: Consumer key and secret are required")
        sys.exit(1)
    
    print(f"Using Consumer Key: {consumer_key}")
    print(f"Using Consumer Secret: {consumer_secret[:5]}...{consumer_secret[-5:]}\n")
    
    # TripIt OAuth endpoints
    request_token_url = "https://api.tripit.com/oauth/request_token"
    
    # Generate OAuth parameters
    print("Generating OAuth parameters...")
    method = "GET"
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    timestamp = str(int(time.time()))
    
    print(f"- OAuth nonce: {nonce}")
    print(f"- OAuth timestamp: {timestamp}")
    
    # Parameters including required oauth_callback for request_token
    params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_version': '1.0',
        'oauth_callback': 'oob'
    }
    
    # Create signature base string
    print("\nGenerating signature base string...")
    # Sort parameters as required
    param_pairs = sorted((quote(k, safe='~'), quote(v, safe='~')) for k, v in params.items())
    param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
    
    # Create base string
    base_string = f"{method.upper()}&{quote(request_token_url, safe='')}&{quote(param_string, safe='')}"
    print(f"- Base string: {base_string}")
    
    # Create signing key
    signing_key = f"{quote(consumer_secret, safe='')}&"
    print(f"- Signing key: {signing_key}")
    
    # Generate signature
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    print(f"- Signature: {signature}")
    
    # Add signature to parameters
    params['oauth_signature'] = signature
    
    # Build authorization header
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(params.items())
    )
    print(f"\nAuthorization header: {auth_header}\n")
    
    # Make the request
    print("\nSending request to TripIt...\n")
    headers = {'Authorization': auth_header}
    
    try:
        # Use httpx with detailed logging
        client = httpx.Client(timeout=30.0)
        response = client.get(request_token_url, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\nRequest successful!")
            response_params = dict(parse_qsl(response.text))
            if 'oauth_token' in response_params and 'oauth_token_secret' in response_params:
                print(f"- OAuth token: {response_params['oauth_token']}")
                print(f"- OAuth token secret: {response_params['oauth_token_secret']}")
            else:
                print("Warning: Expected oauth_token and oauth_token_secret in response")
        else:
            print("\nRequest failed!")
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    debug_tripit_oauth()
