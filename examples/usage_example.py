"""
Example script demonstrating how to use the TripIt MCP server programmatically.
"""

import asyncio
import json
from datetime import datetime, timedelta

import httpx


async def call_mcp_function(server_url: str, function_name: str, arguments: dict):
    """Call an MCP function on the server."""
    async with httpx.AsyncClient() as client:
        payload = {
            "function": function_name,
            "arguments": arguments
        }
        
        response = await client.post(
            f"{server_url}/function",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None


async def main():
    """Run the example."""
    server_url = "http://localhost:8000"
    
    # Example 1: List trips for the current year
    today = datetime.now()
    start_date = f"{today.year}-01-01"
    end_date = f"{today.year}-12-31"
    
    print(f"\nListing trips from {start_date} to {end_date}...\n")
    
    trips_result = await call_mcp_function(
        server_url,
        "list_trips",
        {
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    if trips_result and "trips" in trips_result:
        print(f"Found {len(trips_result['trips'])} trips:")
        for trip in trips_result["trips"]:
            print(f" - {trip['name']} ({trip['start_date']} to {trip['end_date']})")
        
        # Example 2: Get details for the first trip
        if trips_result["trips"]:
            first_trip = trips_result["trips"][0]
            trip_id = first_trip["id"]
            
            print(f"\nGetting details for trip: {first_trip['name']} (ID: {trip_id})...\n")
            
            trip_details = await call_mcp_function(
                server_url,
                "get_trip",
                {"trip_id": trip_id}
            )
            
            if trip_details and "trip" in trip_details:
                print("Trip details:")
                print(json.dumps(trip_details["trip"], indent=2))
            else:
                print("Failed to get trip details.")
    else:
        print("No trips found or error occurred.")


if __name__ == "__main__":
    asyncio.run(main())
