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
        self.consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY", "")
        self.consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET", "")
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN", "")
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET", "")
        
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
    
    def list_trips(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """List trips, optionally filtered by date range."""
        trips = self.client.list_trips(
            start_date=start_date,
            end_date=end_date,
            include_objects=True
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
        if not trip_id:
            raise ValueError("trip_id is required")
        
        return self.client.get_trip(trip_id, include_objects=True)


# Initialize the TripIt service
tripit_service = TripItService()


@app.tool(description="List all trips, optionally filtered by date range")
async def list_trips(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all trips, optionally filtered by date range.
    
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


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the MCP server."""
    import uvicorn
    
    uvicorn.run(app, host=host, port=port)
