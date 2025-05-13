"""
TripIt API client to interact with the TripIt API.
"""

import base64
import hashlib
import hmac
import random
import string
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from urllib.parse import quote, parse_qsl

import httpx
from dateutil import parser as date_parser

from .oauth import TripItOAuth


class TripItAPIError(Exception):
    """Exception raised for errors in the TripIt API."""
    pass


class TripItAPIClient:
    """Client for TripIt API v1."""

    API_BASE_URL = "https://api.tripit.com/v1"
    
    def __init__(self, consumer_key: str, consumer_secret: str, oauth_token: str = None, oauth_token_secret: str = None):
        """
        Initialize the TripIt API client.
        
        Args:
            consumer_key: OAuth consumer key
            consumer_secret: OAuth consumer secret
            oauth_token: OAuth user token (optional)
            oauth_token_secret: OAuth user token secret (optional)
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.client = httpx.Client(timeout=30.0)
    
    def _generate_nonce(self, length: int = 16) -> str:
        """Generate a random nonce for OAuth requests."""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str], token_secret: str = "") -> str:
        """
        Generate OAuth signature for a request.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Request parameters
            token_secret: OAuth token secret for signature key
            
        Returns:
            The OAuth signature
        """
        # Create signature base string exactly per OAuth 1.0a spec
        # 1. Convert params to list of key-value pairs and sort them
        param_pairs = sorted((quote(k, safe='~'), quote(v if v is not None else '', safe='~')) 
                            for k, v in params.items())
        
        # 2. Join each key=value pair with &
        param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
        
        # 3. Create the base string per OAuth spec
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"
        
        # 4. Create the signing key exactly as TripIt expects
        key = f"{quote(self.consumer_secret, safe='')}"
        if token_secret:
            key += f"&{quote(token_secret, safe='')}"
        else:
            key += "&"
        
        # 5. Generate HMAC-SHA1 signature and base64 encode it
        signature = base64.b64encode(
            hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature
    
    def _prepare_oauth_params(self, method: str, url: str, params: Dict[str, str] = None) -> Dict[str, str]:
        """
        Prepare OAuth parameters for a request.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Additional parameters to include in the signature
            
        Returns:
            OAuth parameters
        """
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
        }
        
        # Only include OAuth token if it exists and is not empty
        if self.oauth_token and self.oauth_token.strip():
            oauth_params['oauth_token'] = self.oauth_token
        
        # Combine with additional params for signature generation
        all_params = {}
        if params:
            all_params.update(params)
        all_params.update(oauth_params)
        
        # Generate signature using the token secret if available
        token_secret = self.oauth_token_secret if self.oauth_token_secret and self.oauth_token_secret.strip() else ""
        oauth_params['oauth_signature'] = self._generate_oauth_signature(method, url, all_params, token_secret)
        
        return oauth_params
    
    def _build_authorization_header(self, oauth_params: Dict[str, str]) -> str:
        """
        Build OAuth Authorization header from parameters.
        
        Args:
            oauth_params: OAuth parameters
            
        Returns:
            Authorization header value
        """
        # Format exactly as specified by TripIt API documentation
        # Use proper encoding and format with comma separation
        auth_header = 'OAuth ' + ', '.join(
            f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(oauth_params.items())
        )
        return auth_header
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, str] = None, 
                      data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the TripIt API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response data
        """
        url = f"{self.API_BASE_URL}/{endpoint}"
        
        # Prepare OAuth parameters and authorization header
        oauth_params = self._prepare_oauth_params(method, url, params)
        auth_header = self._build_authorization_header(oauth_params)
        
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json',
        }
        
        # Make the request
        try:
            if method.upper() == 'GET':
                response = self.client.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.client.post(url, params=params, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            error_message = f"TripIt API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_message += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_message += f" - {e.response.text}"
            
            raise TripItAPIError(error_message) from e
        
        except (httpx.RequestError, ValueError) as e:
            raise TripItAPIError(f"Request failed: {str(e)}") from e
    
    def list_trips(self, start_date: Optional[Union[str, datetime]] = None, 
                   end_date: Optional[Union[str, datetime]] = None, 
                   include_objects: bool = True) -> List[Dict[str, Any]]:
        """
        List all trips, optionally filtered by date range.
        
        Args:
            start_date: Start date for filtering trips
            end_date: End date for filtering trips
            include_objects: Whether to include trip objects in the response
            
        Returns:
            List of trips
        """
        params = {
            'format': 'json'
        }
        
        if include_objects:
            params['include_objects'] = 'true'
        
        if start_date:
            if isinstance(start_date, datetime):
                start_date = start_date.strftime('%Y-%m-%d')
            params['start_date'] = start_date
            
        if end_date:
            if isinstance(end_date, datetime):
                end_date = end_date.strftime('%Y-%m-%d')
            params['end_date'] = end_date
        
        response = self._make_request('GET', 'list/trip', params=params)
        
        # Handle the TripIt API response format
        if 'Trip' in response:
            if isinstance(response['Trip'], list):
                return response['Trip']
            else:
                # If there's only one trip, it might be returned as a dict instead of a list
                return [response['Trip']]
        return []
    
    def get_trip(self, trip_id: str, include_objects: bool = True) -> Dict[str, Any]:
        """
        Get details for a specific trip.
        
        Args:
            trip_id: The TripIt trip ID
            include_objects: Whether to include trip objects in the response
            
        Returns:
            Trip details
        """
        params = {
            'format': 'json',
            'id': trip_id
        }
        
        if include_objects:
            params['include_objects'] = 'true'
        
        response = self._make_request('GET', 'get/trip', params=params)
        
        if 'Trip' in response:
            return response['Trip']
        
        raise TripItAPIError(f"Trip with ID {trip_id} not found")
