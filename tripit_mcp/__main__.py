#!/usr/bin/env python3
"""
Entry point for the TripIt MCP server.
"""

import argparse
import os
import sys

from tripit_mcp.server import TripItMCPServer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TripIt MCP Server")
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    return parser.parse_args()


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["TRIPIT_CONSUMER_KEY", "TRIPIT_CONSUMER_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before starting the server.")
        sys.exit(1)


def main():
    """Run the TripIt MCP server."""
    args = parse_args()
    check_environment()
    
    print(f"Starting TripIt MCP server on {args.host}:{args.port}")
    server = TripItMCPServer()
    
    try:
        server.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down TripIt MCP server")
        sys.exit(0)


if __name__ == "__main__":
    main()
