#!/usr/bin/env python3
"""
Entry point for the TripIt MCP server.
"""

import argparse
import os
import sys

from tripit_mcp.server import start_server


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TripIt MCP Server")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["stdio", "http"], 
        default="stdio", 
        help="Server mode: 'stdio' for stdin/stdout communication or 'http' for HTTP server (default: stdio)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="Host to bind the server to when using HTTP mode (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to when using HTTP mode (default: 8000)"
    )
    parser.add_argument(
        "--generate-oauth",
        action="store_true",
        help="Generate OAuth tokens for TripIt API access instead of starting the server"
    )
    return parser.parse_args()


def check_environment():
    """Check if required environment variables are set."""
    # Skip credential check in test mode
    if os.environ.get("TRIPIT_MCP_TEST") == "1":
        sys.stderr.write("Running in test mode, skipping credential check\n")
        return
        
    required_vars = ["TRIPIT_CONSUMER_KEY", "TRIPIT_CONSUMER_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        sys.stderr.write(f"Error: Missing required environment variables: {', '.join(missing_vars)}\n")
        sys.stderr.write("Please set these variables before starting the server.\n")
        sys.exit(1)


def generate_oauth_tokens():
    """Generate OAuth tokens for TripIt API access."""
    from tripit_mcp.oauth import TripItOAuth
    
    # Get API credentials from environment
    consumer_key = os.environ.get('TRIPIT_CONSUMER_KEY')
    consumer_secret = os.environ.get('TRIPIT_CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        sys.stderr.write("Error: TripIt API credentials not found in environment variables.\n")
        sys.stderr.write("Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET.\n")
        sys.exit(1)
    
    try:
        # Initialize OAuth handler and get tokens
        oauth = TripItOAuth(consumer_key, consumer_secret)
        oauth.authorize_app()
    except Exception as e:
        sys.stderr.write(f"OAuth token generation failed: {str(e)}\n")
        sys.exit(1)


def main():
    """Run the TripIt MCP server."""
    args = parse_args()
    
    # If --generate-oauth flag is provided, generate OAuth tokens and exit
    if args.generate_oauth:
        generate_oauth_tokens()
        return
    
    check_environment()
    
    # Use stderr for informational messages so they don't interfere with stdio protocol
    sys.stderr.write(f"Starting TripIt MCP server in {args.mode} mode\n")
    if args.mode == "http":
        sys.stderr.write(f"HTTP server will be available at http://{args.host}:{args.port}\n")
        
    try:
        start_server(mode=args.mode, host=args.host, port=args.port)
    except KeyboardInterrupt:
        sys.stderr.write("\nShutting down TripIt MCP server\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
