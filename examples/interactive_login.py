#!/usr/bin/env python
"""
TripIt MCP Interactive Login Example

This example demonstrates how to use the interactive OAuth login flow
with the TripIt MCP Server. This approach allows you to authenticate
with TripIt directly through the MCP, without needing to pre-generate
OAuth tokens.

Usage:
    python interactive_login.py
"""

import json
import os
import subprocess
import sys
import time
import webbrowser
from typing import Dict, Any, Optional


def send_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a request to the MCP server and get the response.
    
    Args:
        request: The MCP request to send
        
    Returns:
        The MCP response
    """
    # Convert request to JSON
    json_request = json.dumps(request)
    print(f"Sending request: {json_request}", file=sys.stderr)
    
    # Write to stdout and flush
    print(json_request, flush=True)
    
    # Read response
    response_line = sys.stdin.readline()
    if not response_line:
        print("Error: No response received", file=sys.stderr)
        sys.exit(1)
    
    # Parse response
    try:
        response = json.loads(response_line)
        print(f"Received response: {json.dumps(response, indent=2)}", file=sys.stderr)
        return response
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON response: {response_line}", file=sys.stderr)
        sys.exit(1)


def tripit_login() -> Dict[str, Any]:
    """
    Initiate the TripIt OAuth login process.
    
    Returns:
        The response from the tripit_login tool
    """
    print("\n--- Step 1: Initiating TripIt OAuth Login ---", file=sys.stderr)
    
    request = {
        "function": "tripit_login",
        "arguments": {}
    }
    
    return send_request(request)


def tripit_login_complete(request_token: str, request_token_secret: str) -> Dict[str, Any]:
    """
    Complete the TripIt OAuth login process.
    
    Args:
        request_token: The request token from tripit_login
        request_token_secret: The request token secret from tripit_login
        
    Returns:
        The response from the tripit_login_complete tool
    """
    print("\n--- Step 3: Completing TripIt OAuth Login ---", file=sys.stderr)
    
    request = {
        "function": "tripit_login_complete",
        "arguments": {
            "request_token": request_token,
            "request_token_secret": request_token_secret
        }
    }
    
    return send_request(request)


def check_auth_status() -> Dict[str, Any]:
    """
    Check if authenticated with TripIt.
    
    Returns:
        The response from the tripit_auth_status tool
    """
    print("\n--- Checking TripIt Authentication Status ---", file=sys.stderr)
    
    request = {
        "function": "tripit_auth_status",
        "arguments": {}
    }
    
    return send_request(request)


def list_trips(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    List TripIt trips.
    
    Args:
        start_date: Optional start date for filtering trips
        end_date: Optional end date for filtering trips
        
    Returns:
        The response from the list_trips tool
    """
    print("\n--- Listing TripIt Trips ---", file=sys.stderr)
    
    request = {
        "function": "list_trips",
        "arguments": {}
    }
    
    if start_date:
        request["arguments"]["start_date"] = start_date
    
    if end_date:
        request["arguments"]["end_date"] = end_date
    
    return send_request(request)


def get_trip(trip_id: str) -> Dict[str, Any]:
    """
    Get details for a specific trip.
    
    Args:
        trip_id: The TripIt trip ID
        
    Returns:
        The response from the get_trip tool
    """
    print(f"\n--- Getting TripIt Trip {trip_id} ---", file=sys.stderr)
    
    request = {
        "function": "get_trip",
        "arguments": {
            "trip_id": trip_id
        }
    }
    
    return send_request(request)


def start_mcp_server() -> subprocess.Popen:
    """
    Start the TripIt MCP server as a subprocess.
    
    Returns:
        The subprocess handle
    """
    print("Starting TripIt MCP server...", file=sys.stderr)
    
    # Start the server in stdio mode
    process = subprocess.Popen(
        ["python", "-m", "tripit_mcp", "--mode", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # Redirect stderr to devnull to avoid cluttering the output
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Give it a moment to start up
    time.sleep(1)
    
    return process


def main():
    """Run the interactive login example."""
    print("TripIt MCP Interactive Login Example", file=sys.stderr)
    print("===================================", file=sys.stderr)
    
    # Save the original stdin and stdout
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    
    # Start the server
    process = start_mcp_server()
    
    try:
        # Redirect stdin and stdout to the server's pipes
        sys.stdin = process.stdout
        sys.stdout = process.stdin
        
        # Check if we're already authenticated
        status = check_auth_status()
        
        if status.get("authenticated", False):
            print("\nAlready authenticated with TripIt!", file=sys.stderr)
        else:
            # Start the login process
            login_response = tripit_login()
            
            if "error" in login_response:
                print(f"\nError during login: {login_response['error']}", file=sys.stderr)
                sys.exit(1)
            
            # Extract request tokens and authorization URL
            request_token = login_response.get("request_token")
            request_token_secret = login_response.get("request_token_secret")
            instructions = login_response.get("instructions", [])
            
            # Display instructions
            print("\n--- Step 2: User Authorization ---", file=sys.stderr)
            for instruction in instructions:
                print(instruction, file=sys.stderr)
                # If this line looks like a URL, try to open it in a browser
                if instruction.startswith("http"):
                    webbrowser.open(instruction)
            
            # Wait for user to authorize
            input("\nAfter authorizing in your browser, press Enter to continue...\n")
            
            # Complete the login process
            complete_response = tripit_login_complete(request_token, request_token_secret)
            
            if complete_response.get("authenticated", False):
                print("\nSuccessfully authenticated with TripIt!", file=sys.stderr)
            else:
                print(f"\nAuthentication failed: {complete_response.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
        
        # Now let's use the API to list trips
        trips_response = list_trips()
        
        if "error" in trips_response:
            print(f"\nError listing trips: {trips_response['error']}", file=sys.stderr)
        else:
            trips = trips_response.get("trips", [])
            print(f"\nFound {len(trips)} trips in your TripIt account:", file=sys.stderr)
            
            for i, trip in enumerate(trips[:5], 1):  # Show up to 5 trips
                print(f"{i}. {trip.get('name')} ({trip.get('start_date')} to {trip.get('end_date')})", file=sys.stderr)
            
            # If we have trips, get details for the first one
            if trips:
                trip_id = trips[0].get("id")
                if trip_id:
                    trip_response = get_trip(trip_id)
                    
                    if "error" in trip_response:
                        print(f"\nError getting trip details: {trip_response['error']}", file=sys.stderr)
                    else:
                        trip = trip_response.get("trip", {})
                        print(f"\nTrip Details for '{trip.get('display_name')}':", file=sys.stderr)
                        print(f"  ID: {trip.get('id')}", file=sys.stderr)
                        print(f"  Dates: {trip.get('start_date')} to {trip.get('end_date')}", file=sys.stderr)
                        print(f"  Primary Location: {trip.get('primary_location')}", file=sys.stderr)
                        
                        # Show segments if available
                        if "Segments" in trip:
                            print(f"  Segments: {len(trip['Segments'])}", file=sys.stderr)
        
        print("\nInteractive login example completed successfully!", file=sys.stderr)
    
    finally:
        # Restore the original stdin and stdout
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        
        # Terminate the server
        print("Shutting down TripIt MCP server...", file=sys.stderr)
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
