"""
FastMCP server implementation for TripIt API using FastMCP v2.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastmcp import FastMCP

from .tripit_client import TripItAPIClient, TripItAPIError
from .oauth import TripItOAuth


# Initialize FastMCP application
app = FastMCP(
    title="TripIt MCP Server",
    description="A Model Context Protocol (MCP) server that provides access to your TripIt trip data",
    contact={
        "name": "TripIt MCP Admin",
        "email": "admin@example.com"
    }
)


class TripItService:
    """Service class for TripIt API operations."""
    
    def __init__(self):
        """Initialize the TripIt service."""
        # Get TripIt API credentials from environment variables
        self.consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY", None)
        self.consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET", None)
        
        # Get OAuth tokens from environment variables initially, but they can be updated via login
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN", None)
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET", None)
        
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("TripIt API credentials not found in environment variables. "
                           "Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET.")
        
        # Initialize the TripIt API client
        self.refresh_client()
    
    def refresh_client(self):
        """Initialize or refresh the TripIt API client with current tokens."""
        self.client = TripItAPIClient(
            self.consumer_key, 
            self.consumer_secret,
            self.oauth_token,
            self.oauth_token_secret
        )
    
    def set_oauth_tokens(self, oauth_token: str, oauth_token_secret: str):
        """
        Set OAuth tokens and refresh the API client.
        
        Args:
            oauth_token: TripIt OAuth token
            oauth_token_secret: TripIt OAuth token secret
        """
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.refresh_client()
    
    def is_authenticated(self) -> bool:
        """
        Check if OAuth tokens are available.
        
        Returns:
            True if OAuth tokens are available, False otherwise
        """
        return bool(self.oauth_token and self.oauth_token_secret)
    
    def verify_tokens(self) -> bool:
        """
        Verify that the OAuth tokens are valid by making a test API call.
        
        Returns:
            True if tokens are valid, False otherwise
        """
        if not self.is_authenticated():
            return False
            
        try:
            # Make a lightweight API call to check token validity
            self.client.list_trips(include_objects=False)
            return True
        except Exception:
            return False
    
    def list_trips(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                  include_objects: bool = True) -> List[Dict[str, Any]]:
        """List trips, optionally filtered by date range."""
        if not self.is_authenticated():
            raise ValueError("OAuth authentication required. Please use the 'tripit_login' tool first.")
            
        trips = self.client.list_trips(
            start_date=start_date,
            end_date=end_date,
            include_objects=include_objects
        )
        
        # Extract relevant trip information
        formatted_trips = []
        for trip in trips:
            formatted_trip = {
                "id": trip.get("id"),
                "name": trip.get("display_name"),
                "start_date": trip.get("start_date"),
                "end_date": trip.get("end_date"),
                "primary_location": trip.get("primary_location"),
                "is_private": trip.get("is_private") == "true"
            }
            formatted_trips.append(formatted_trip)
        
        return formatted_trips
    
    def get_trip(self, trip_id: str) -> Dict[str, Any]:
        """Get details for a specific trip."""
        if not self.is_authenticated():
            raise ValueError("OAuth authentication required. Please use the 'tripit_login' tool first.")
            
        if not trip_id:
            raise ValueError("trip_id is required")
        
        return self.client.get_trip(trip_id, include_objects=True)


# Initialize the TripIt service
tripit_service = TripItService()


@app.tool(description="Authenticate with TripIt API using OAuth. This tool must be called before using other TripIt tools.")
async def tripit_login() -> Dict[str, Any]:
    """
    Authenticate with TripIt API using OAuth 1.0a.
    
    This tool guides you through the OAuth authentication process:
    1. Obtains a request token from TripIt
    2. Provides a URL for you to authorize access to your TripIt account
    3. Exchanges the authorized token for an access token
    4. Stores the tokens for subsequent API calls
    
    You must complete this authentication flow before using other TripIt tools.
    
    Returns:
        Status of the authentication process
    """
    try:
        # Get API credentials from service
        consumer_key = tripit_service.consumer_key
        consumer_secret = tripit_service.consumer_secret
        
        # Create OAuth handler
        oauth = TripItOAuth(consumer_key, consumer_secret)
        
        # Step 1: Get request token
        request_token, request_token_secret = oauth.get_request_token()
        
        # Step 2: Get authorization URL
        auth_url = oauth.get_authorization_url(request_token)
        
        # Provide instructions to user
        return {
            "status": "authorization_needed",
            "message": "Please authorize access to your TripIt account",
            "instructions": [
                "1. Go to the following URL in your browser:",
                auth_url,
                "2. Log in to TripIt (if needed) and authorize the application",
                "3. Once authorized, return here and call tripit_login_complete"
            ],
            "request_token": request_token,
            "request_token_secret": request_token_secret
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.tool(description="Complete the TripIt authentication process after authorization.")
async def tripit_login_complete(
    request_token: str,
    request_token_secret: str
) -> Dict[str, Any]:
    """
    Complete the TripIt authentication process after authorization.
    
    This tool should be called after you've authorized the application in your browser.
    It exchanges the authorized request token for an access token and stores it for future API calls.
    
    Args:
        request_token: The request token from tripit_login
        request_token_secret: The request token secret from tripit_login
        
    Returns:
        Status of the authentication process
    """
    try:
        # Get API credentials from service
        consumer_key = tripit_service.consumer_key
        consumer_secret = tripit_service.consumer_secret
        
        # Create OAuth handler
        oauth = TripItOAuth(consumer_key, consumer_secret)
        
        # Exchange request token for access token
        access_token, access_token_secret = oauth.get_access_token(request_token, request_token_secret)
        
        # Store tokens in service
        tripit_service.set_oauth_tokens(access_token, access_token_secret)
        
        # Test the tokens
        oauth.test_tokens(access_token, access_token_secret)
        
        return {
            "status": "authenticated",
            "message": "Successfully authenticated with TripIt",
            "authenticated": True
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "authenticated": False
        }


@app.tool(description="Check if you are authenticated with TripIt")
async def tripit_auth_status() -> Dict[str, Any]:
    """
    Check if you are authenticated with TripIt API.
    
    Returns the current authentication status and instructions if not authenticated.
    
    Returns:
        Authentication status information
    """
    is_authenticated = tripit_service.is_authenticated()
    
    if is_authenticated:
        # If authenticated, verify tokens are still valid
        tokens_valid = tripit_service.verify_tokens()
        if tokens_valid:
            return {
                "authenticated": True,
                "message": "You are authenticated with TripIt API and tokens are valid"
            }
        else:
            return {
                "authenticated": False,
                "message": "Authentication tokens exist but appear to be invalid",
                "instructions": "Please call tripit_login to re-authenticate"
            }
    else:
        return {
            "authenticated": False,
            "message": "You are not authenticated with TripIt API",
            "instructions": "Please call tripit_login to authenticate"
        }


@app.tool(description="List all trips, optionally filtered by date range. Requires authentication via tripit_login first.")
async def list_trips(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all trips, optionally filtered by date range.
    
    Note: You must call tripit_login first to authenticate with TripIt.
    
    Args:
        start_date: Optional start date for filtering trips (YYYY-MM-DD)
        end_date: Optional end date for filtering trips (YYYY-MM-DD)
        
    Returns:
        Dictionary containing a list of trips with basic information
    """
    try:
        trips = tripit_service.list_trips(start_date, end_date)
        return {"trips": trips}
    except TripItAPIError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}


@app.tool(description="Get details for a specific trip. Requires authentication via tripit_login first.")
async def get_trip(
    trip_id: str
) -> Dict[str, Any]:
    """
    Get details for a specific trip.
    
    Note: You must call tripit_login first to authenticate with TripIt.
    
    Args:
        trip_id: The TripIt trip ID
        
    Returns:
        Dictionary containing all trip details
    """
    try:
        trip = tripit_service.get_trip(trip_id)
        return {"trip": trip}
    except TripItAPIError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}


def start_server(mode: str = "stdio", host: str = "0.0.0.0", port: int = 8000):
    """
    Start the MCP server in the specified mode.
    
    Args:
        mode: The server mode - "stdio" (default) or "http"
        host: Host to bind to when using HTTP mode
        port: Port to bind to when using HTTP mode
    """
    import sys
    import logging
    
    # Configure logging to use stderr instead of stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )
    
    if mode == "stdio":
        # Start in stdio mode (stdin/stdout communication)
        import asyncio
        import json
        import sys
        
        # Debug message to stderr
        sys.stderr.write("Starting stdio mode with FastMCP\n")
        # Normal operation
        asyncio.run(app.run_stdio_async())
    else:
        # Start in HTTP mode
        import uvicorn
        uvicorn.run(app, host=host, port=port, log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": True,
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": sys.stderr,
                }
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
        })
