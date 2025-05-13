#!/usr/bin/env python
"""
TripIt MCP Interactive Login Test

This script tests the new interactive login functionality in the TripIt MCP server.
It checks if the OAuth flow works properly by:
1. Starting the MCP server
2. Initiating the OAuth login process
3. Simulating user authorization
4. Completing the login flow
5. Testing API access with the authenticated session

Usage:
    TRIPIT_CONSUMER_KEY=xxx TRIPIT_CONSUMER_SECRET=yyy python test_interactive_login.py
"""

import json
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional, Tuple


class MCPClient:
    """Simple MCP client to communicate with the server."""

    def __init__(self, server_process):
        """Initialize the client with a server process."""
        self.process = server_process
        self.original_stdin = sys.stdin
        self.original_stdout = sys.stdout
        # Redirect stdin/stdout to the server process
        sys.stdin = self.process.stdout
        sys.stdout = self.process.stdin

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Restore stdin/stdout
        sys.stdin = self.original_stdin
        sys.stdout = self.original_stdout
        return False  # Don't suppress exceptions

    def call(self, function: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP function."""
        request = {
            "function": function,
            "arguments": kwargs
        }
        
        # Convert request to JSON
        json_request = json.dumps(request)
        print(f"Sending request: {json_request}", file=sys.stderr)
        
        # Send the request
        print(json_request, flush=True)
        
        # Read the response
        response_line = sys.stdin.readline()
        if not response_line:
            raise RuntimeError("No response received")
        
        # Parse the response
        try:
            response = json.loads(response_line)
            print(f"Received response: {json.dumps(response, indent=2)}", file=sys.stderr)
            return response
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response: {response_line}")


def start_server() -> subprocess.Popen:
    """Start the TripIt MCP server."""
    print("Starting TripIt MCP server...", file=sys.stderr)
    
    # Check that required environment variables are set
    for var in ["TRIPIT_CONSUMER_KEY", "TRIPIT_CONSUMER_SECRET"]:
        if not os.environ.get(var):
            print(f"Error: {var} environment variable is not set", file=sys.stderr)
            sys.exit(1)
    
    # Start the server in stdio mode
    process = subprocess.Popen(
        ["python", "-m", "tripit_mcp", "--mode", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Capture stderr for debugging
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Give it a moment to start up
    time.sleep(1)
    
    return process


def test_authentication(client: MCPClient) -> Tuple[bool, str, str]:
    """
    Test the authentication flow.
    
    Args:
        client: MCP client
        
    Returns:
        Tuple of (success, request_token, request_token_secret)
    """
    print("\n=== Testing Authentication ===", file=sys.stderr)
    
    # First check if already authenticated
    auth_status = client.call("tripit_auth_status")
    if auth_status.get("authenticated", False):
        print("Already authenticated with TripIt", file=sys.stderr)
        return True, "", ""
    
    # Start the login process
    try:
        login_response = client.call("tripit_login")
        
        if "error" in login_response:
            print(f"Error during login: {login_response['error']}", file=sys.stderr)
            return False, "", ""
        
        # Extract request tokens and URL
        request_token = login_response.get("request_token", "")
        request_token_secret = login_response.get("request_token_secret", "")
        
        if not request_token or not request_token_secret:
            print("Error: Missing token information in response", file=sys.stderr)
            return False, "", ""
            
        # Print instructions for manual testing
        print("\n=== Manual Testing Instructions ===", file=sys.stderr)
        print("To complete the test manually:", file=sys.stderr)
        for instruction in login_response.get("instructions", []):
            print(instruction, file=sys.stderr)
            
        return True, request_token, request_token_secret
        
    except Exception as e:
        print(f"Error during authentication test: {str(e)}", file=sys.stderr)
        return False, "", ""


def main():
    """Run the test."""
    print("TripIt MCP Interactive Login Test", file=sys.stderr)
    print("===============================", file=sys.stderr)
    
    process = start_server()
    
    try:
        # Create MCP client
        with MCPClient(process) as client:
            # Test authentication
            success, request_token, request_token_secret = test_authentication(client)
            
            if not success:
                print("\nAuthentication test failed", file=sys.stderr)
                return
            
            if request_token and request_token_secret:
                print("\n=== Authentication Process Started Successfully! ===", file=sys.stderr)
                print("\nTo complete the authentication flow, you would:", file=sys.stderr)
                print("1. Authorize the application in your browser", file=sys.stderr)
                print("2. Call tripit_login_complete with the request tokens", file=sys.stderr)
                print("3. Make API calls like list_trips", file=sys.stderr)
                
                # For manual testing, print the request token info
                print("\nRequest Token:", request_token, file=sys.stderr)
                print("Request Token Secret:", request_token_secret, file=sys.stderr)
                
                # Give option to continue with manual testing
                should_continue = input("\nWould you like to continue with manual authorization? (y/n): ")
                if should_continue.lower() == "y":
                    print("\nPlease authorize the application in your browser using the URL above", file=sys.stderr)
                    input("Press Enter when you have completed the authorization...")
                    
                    # Complete the login process
                    complete_response = client.call(
                        "tripit_login_complete",
                        request_token=request_token,
                        request_token_secret=request_token_secret
                    )
                    
                    if complete_response.get("authenticated", False):
                        print("\nAuthentication successful!", file=sys.stderr)
                        
                        # Try listing trips
                        print("\n=== Testing API Access ===", file=sys.stderr)
                        trips_response = client.call("list_trips")
                        
                        if "error" in trips_response:
                            print(f"Error listing trips: {trips_response['error']}", file=sys.stderr)
                        else:
                            trips = trips_response.get("trips", [])
                            print(f"Success! Found {len(trips)} trips", file=sys.stderr)
                    else:
                        print(f"\nAuthentication failed: {complete_response.get('error', 'Unknown error')}", file=sys.stderr)
            else:
                print("\nServer appears to be working but no authorization needed", file=sys.stderr)
                
    finally:
        # Terminate the server
        print("\nShutting down TripIt MCP server...", file=sys.stderr)
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
