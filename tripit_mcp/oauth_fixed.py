"""
OAuth authentication module for the TripIt API.

This module handles the OAuth 1.0a authentication flow for TripIt API
with strict RFC 3986 encoding and OAuth 1.0a specification compliance.
"""

import base64
import hashlib
import hmac
import os
import random
import string
import time
import webbrowser
from typing import Dict, Tuple, Optional
from urllib.parse import quote, parse_qsl

import httpx


class TripItOAuth:
    """OAuth 1.0a implementation for TripIt API."""

    REQUEST_TOKEN_URL = "https://api.tripit.com/oauth/request_token"
    AUTHORIZE_URL = "https://www.tripit.com/oauth/authorize"
    ACCESS_TOKEN_URL = "https://api.tripit.com/oauth/access_token"
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        """
        Initialize the OAuth handler.
        
        Args:
            consumer_key: TripIt API consumer key
            consumer_secret: TripIt API consumer secret
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        
        # Configure httpx client with appropriate settings
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'TripIt-MCP/1.0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': '*/*'
            }
        )
    
    def _generate_nonce(self, length: int = 32) -> str:
        """Generate a random nonce for OAuth requests."""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str], 
                                  token_secret: str = "") -> str:
        """
        Generate OAuth signature for a request.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Request parameters
            token_secret: OAuth token secret (empty for request token)
            
        Returns:
            The OAuth signature
        """
        # RFC 3986 encoding for all parameters
        param_pairs = []
        for k, v in sorted(params.items()):
            # Encode key and value separately per RFC 3986
            k_enc = quote(str(k), safe='')
            v_enc = quote(str(v) if v is not None else '', safe='')
            param_pairs.append(f"{k_enc}={v_enc}")
        
        # Join with & to create parameter string
        param_string = '&'.join(param_pairs)
        
        # Create base string exactly per OAuth 1.0a spec
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"
        
        # Create signing key - TripIt expects consumer_secret&token_secret (or just & if no token)
        key = f"{quote(self.consumer_secret, safe='')}&{quote(token_secret, safe='')}"
        
        # Generate HMAC-SHA1 signature using the key and base string
        signature = base64.b64encode(
            hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature
    
    def _build_authorization_header(self, oauth_params: Dict[str, str]) -> str:
        """
        Build OAuth Authorization header from parameters.
        
        Args:
            oauth_params: OAuth parameters
            
        Returns:
            Authorization header value
        """
        # Format exactly as specified by OAuth 1.0a spec
        auth_header_parts = []
        for k, v in sorted(oauth_params.items()):
            auth_header_parts.append(f'{quote(k, safe="")}="{quote(v, safe="~")}"')
        
        return 'OAuth ' + ', '.join(auth_header_parts)
    
    def get_request_token(self) -> Tuple[str, str]:
        """
        Get a request token from TripIt.
        
        Returns:
            Tuple of (oauth_token, oauth_token_secret)
        """
        # Create OAuth parameters with a callback
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
            'oauth_callback': 'oob'  # Required for OAuth 1.0a
        }
        
        # Generate signature with all parameters
        oauth_params['oauth_signature'] = self._generate_oauth_signature(
            'GET', self.REQUEST_TOKEN_URL, oauth_params
        )
        
        # Build authorization header
        auth_header = self._build_authorization_header(oauth_params)
        
        headers = {
            'Authorization': auth_header
        }
        
        try:
            # Log the request details for debugging
            print(f"Requesting token from: {self.REQUEST_TOKEN_URL}")
            print(f"Authorization header: {auth_header}")
            
            # Make request with oauth_callback in both header and query parameters
            params = {'oauth_callback': 'oob'}
            response = self.client.get(self.REQUEST_TOKEN_URL, headers=headers, params=params)
            
            # Print response details for debugging
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            content = response.text
            print(f"Response Content: {content!r}")
            
            response.raise_for_status()
            
            # Handle empty response
            if not content.strip():
                raise ValueError("Empty response received from TripIt API")
            
            # Parse response parameters
            response_params = dict(parse_qsl(content))
            print(f"Parsed Response Parameters: {response_params}")
            
            # Validate response
            if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
                raise ValueError(f"Invalid response from request_token: {content}")
            
            oauth_token = response_params['oauth_token']
            oauth_token_secret = response_params['oauth_token_secret']
            
            print(f"Successfully obtained request token: {oauth_token}")
            return oauth_token, oauth_token_secret
        
        except httpx.HTTPStatusError as e:
            error_detail = f"Failed to get request token: {e.response.status_code} - {e.response.text}"
            print(f"Error: {error_detail}")
            raise ValueError(error_detail)
        except httpx.RequestError as e:
            error_detail = f"Request error: {str(e)}"
            print(f"Error: {error_detail}")
            raise ValueError(error_detail)
    
    def get_authorization_url(self, oauth_token: str) -> str:
        """
        Get the authorization URL for the user to authorize the token.
        
        Args:
            oauth_token: The request token from get_request_token
            
        Returns:
            The authorization URL
        """
        return f"{self.AUTHORIZE_URL}?oauth_token={quote(oauth_token, safe='')}"
    
    def get_access_token(self, oauth_token: str, oauth_token_secret: str) -> Tuple[str, str]:
        """
        Exchange the authorized request token for an access token.
        
        Args:
            oauth_token: The authorized request token
            oauth_token_secret: The request token secret
            
        Returns:
            Tuple of (access_token, access_token_secret)
        """
        # Create OAuth parameters for access token request
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_token': oauth_token,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
        }
        
        # Generate signature
        oauth_params['oauth_signature'] = self._generate_oauth_signature(
            'GET', self.ACCESS_TOKEN_URL, oauth_params, oauth_token_secret
        )
        
        # Build authorization header
        auth_header = self._build_authorization_header(oauth_params)
        
        headers = {
            'Authorization': auth_header
        }
        
        try:
            # Log the request details for debugging
            print(f"Exchanging for access token from: {self.ACCESS_TOKEN_URL}")
            print(f"Using token: {oauth_token}")
            print(f"Authorization header: {auth_header}")
            
            # Make the request
            response = self.client.get(self.ACCESS_TOKEN_URL, headers=headers)
            
            # Print response details for debugging
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            response_text = response.text
            print(f"Response Text: {response_text!r}")
            
            response.raise_for_status()
            
            # Parse response
            response_params = dict(parse_qsl(response_text))
            print(f"Parsed Response Parameters: {response_params}")
            
            # Validate response
            if 'oauth_token' not in response_params or 'oauth_token_secret' not in response_params:
                raise ValueError(f"Invalid response from access_token: {response_text}")
            
            access_token = response_params['oauth_token']
            access_token_secret = response_params['oauth_token_secret']
            
            print(f"Successfully obtained access token: {access_token}")
            return access_token, access_token_secret
            
        except httpx.HTTPStatusError as e:
            error_detail = f"Failed to get access token: {e.response.status_code} - {e.response.text}"
            print(f"Error: {error_detail}")
            raise ValueError(error_detail)
        except httpx.RequestError as e:
            error_detail = f"Request error: {str(e)}"
            print(f"Error: {error_detail}")
            raise ValueError(error_detail)
    
    def authorize_app(self) -> Tuple[str, str]:
        """
        Complete the full OAuth authorization flow.
        
        This will:
        1. Get a request token
        2. Open a browser for the user to authorize
        3. Wait for user confirmation
        4. Exchange for an access token
        
        Returns:
            Tuple of (access_token, access_token_secret)
        """
        print("\n=== TripIt OAuth Authorization Process ===\n")
        
        print("Step 1: Getting request token from TripIt...")
        # Step 1: Get request token
        request_token, request_token_secret = self.get_request_token()
        
        # Step 2: Direct user to authorization page
        auth_url = self.get_authorization_url(request_token)
        print("\nStep 2: Directing you to TripIt's authorization page...")
        print(f"Authorization URL: {auth_url}")
        print("Your browser will open. Please log in to TripIt if needed and authorize the application.")
        
        # Wait briefly to ensure console output is visible before browser opens
        time.sleep(1)
        webbrowser.open(auth_url)
        
        # Step 3: Wait for user to authorize
        print("\nStep 3: Waiting for authorization...")
        print("Once you've authorized the application in your browser,")
        input("press Enter to continue the OAuth process...\n")
        
        # Step 4: Exchange for access token
        print("Step 4: Exchanging request token for access token...")
        access_token, access_token_secret = self.get_access_token(request_token, request_token_secret)
        
        print("\n=== OAuth Authorization Complete! ===\n")
        print("Your OAuth tokens have been successfully generated.")
        print("To use these tokens with the TripIt MCP Server, add them to your .env file:\n")
        print(f"TRIPIT_OAUTH_TOKEN={access_token}")
        print(f"TRIPIT_OAUTH_TOKEN_SECRET={access_token_secret}\n")
        
        return access_token, access_token_secret


def main():
    """Command-line utility to get OAuth tokens."""
    print("TripIt OAuth Token Generator")
    print("===========================")
    
    # Get credentials from environment or prompt
    consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY")
    consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET")
    
    if not consumer_key:
        consumer_key = input("Enter your TripIt API Consumer Key: ")
    
    if not consumer_secret:
        consumer_secret = input("Enter your TripIt API Consumer Secret: ")
    
    if not consumer_key or not consumer_secret:
        print("Error: Consumer key and secret are required")
        return
    
    try:
        oauth = TripItOAuth(consumer_key, consumer_secret)
        access_token, access_token_secret = oauth.authorize_app()
        
        # Test if the tokens work
        should_test = input("\nWould you like to verify the tokens with a test API call? (y/n): ")
        if should_test.lower() == 'y':
            from .tripit_client import TripItAPIClient
            client = TripItAPIClient(
                consumer_key, 
                consumer_secret,
                access_token,
                access_token_secret
            )
            print("\nTesting API access...")
            try:
                trips = client.list_trips()
                print(f"Success! Found {len(trips)} trips in your account.")
            except Exception as e:
                print(f"API test failed: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
