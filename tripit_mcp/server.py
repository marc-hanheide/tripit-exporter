"""
FastMCP server implementation for TripIt API.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastmcp import MCPRouter, run_server
from fastmcp.models import (
    FunctionDefinition, 
    Parameter, 
    ParameterType, 
    RequestWithMetadata,
    MCPResponse
)

from .tripit_client import TripItAPIClient, TripItAPIError


class TripItMCPServer:
    """MCP server for TripIt API."""

    def __init__(self):
        """Initialize the TripIt MCP server."""
        # Get TripIt API credentials from environment variables
        self.consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY", "")
        self.consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET", "")
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN", "")
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET", "")
        
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("TripIt API credentials not found in environment variables. "
                            "Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET.")
        
        # Initialize the TripIt API client
        self.tripit_client = TripItAPIClient(
            self.consumer_key, 
            self.consumer_secret,
            self.oauth_token,
            self.oauth_token_secret
        )
        
        # Create MCP router
        self.router = MCPRouter()
        self._register_functions()

    def _register_functions(self):
        """Register MCP functions."""
        
        @self.router.function(
            name="list_trips",
            description="List all trips, optionally filtered by date range",
            parameters=[
                Parameter(
                    name="start_date",
                    description="Start date for filtering trips (YYYY-MM-DD)",
                    type=ParameterType.STRING,
                    required=False
                ),
                Parameter(
                    name="end_date",
                    description="End date for filtering trips (YYYY-MM-DD)",
                    type=ParameterType.STRING,
                    required=False
                )
            ]
        )
        async def list_trips(request: RequestWithMetadata) -> MCPResponse:
            """List all trips, optionally filtered by date range."""
            try:
                params = request.parsed_arguments
                start_date = params.get("start_date")
                end_date = params.get("end_date")
                
                trips = self.tripit_client.list_trips(
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
                
                return MCPResponse({"trips": formatted_trips})
            
            except TripItAPIError as e:
                return MCPResponse({"error": str(e)}, status_code=500)
        
        @self.router.function(
            name="get_trip",
            description="Get details for a specific trip",
            parameters=[
                Parameter(
                    name="trip_id",
                    description="The TripIt trip ID",
                    type=ParameterType.STRING,
                    required=True
                )
            ]
        )
        async def get_trip(request: RequestWithMetadata) -> MCPResponse:
            """Get details for a specific trip."""
            try:
                params = request.parsed_arguments
                trip_id = params.get("trip_id")
                
                if not trip_id:
                    return MCPResponse({"error": "trip_id is required"}, status_code=400)
                
                trip = self.tripit_client.get_trip(trip_id, include_objects=True)
                
                return MCPResponse({"trip": trip})
            
            except TripItAPIError as e:
                return MCPResponse({"error": str(e)}, status_code=500)
    
    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the MCP server."""
        run_server(
            router=self.router,
            host=host,
            port=port
        )


def main():
    """Run the TripIt MCP server."""
    server = TripItMCPServer()
    server.start()
