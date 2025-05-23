"""
FastMCP server implementation for TripIt API using FastMCP v2.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastmcp import FastMCP

from .tripit_client import TripItAPIClient, TripItAPIError


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
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN", None)
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET", None)
        
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("TripIt API credentials not found in environment variables. "
                           "Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET.")
        
        # Initialize the TripIt API client
        self.client = TripItAPIClient(
            self.consumer_key, 
            self.consumer_secret,
            self.oauth_token,
            self.oauth_token_secret
        )
    
    def list_trips(self, past: bool = False) -> List[Dict[str, Any]]:
        """List trips, either past or current/future trips."""
        trips_data = self.client.list_trips(
            past=past,
            include_objects=True
        )
        
        # Extract relevant trip information
        formatted_trips = []
        for trip in trips_data['trips']:
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
        if not trip_id:
            raise ValueError("trip_id is required")
        
        return self.client.get_trip(trip_id, include_objects=True)


# Initialize the TripIt service
tripit_service = TripItService()


@app.tool(description="List trips with pagination support, either past or current/future")
async def list_trips(
    past: bool = False,
    page_num: Optional[int] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    List trips with pagination support, either past or current/future.
    
    Args:
        past: If True, returns past trips. If False, returns current and future trips.
        page_num: Page number for pagination (positive integer)
        page_size: Number of items per page (positive integer)
        
    Returns:
        Dictionary containing a list of trips with basic information and pagination metadata
    """
    try:
        # Call the updated TripIt service method with pagination parameters
        trips_data = tripit_service.client.list_trips(
            past=past,
            include_objects=True,
            page_num=page_num,
            page_size=page_size
        )
        
        # Extract relevant trip information
        formatted_trips = []
        for trip in trips_data['trips']:
            formatted_trip = {
                "id": trip.get("id"),
                "name": trip.get("display_name"),
                "start_date": trip.get("start_date"),
                "end_date": trip.get("end_date"),
                "primary_location": trip.get("primary_location"),
                "is_private": trip.get("is_private") == "true"
            }
            formatted_trips.append(formatted_trip)
        
        # Return the formatted trips along with pagination metadata
        return {
            "trips": formatted_trips,
            "pagination": trips_data['pagination']
        }
    except TripItAPIError as e:
        return {"error": str(e)}


@app.tool(description="Get details for a specific trip")
async def get_trip(
    trip_id: str
) -> Dict[str, Any]:
    """
    Get details for a specific trip.
    
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
