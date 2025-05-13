#!/usr/bin/env python3
"""
Command-line utility to generate OAuth tokens for the TripIt API.
"""

import argparse
import os
import sys

from tripit_mcp.oauth import TripItOAuth


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate OAuth tokens for TripIt API")
    
    parser.add_argument(
        "--consumer-key",
        help="TripIt API Consumer Key (can also be set as TRIPIT_CONSUMER_KEY environment variable)"
    )
    
    parser.add_argument(
        "--consumer-secret",
        help="TripIt API Consumer Secret (can also be set as TRIPIT_CONSUMER_SECRET environment variable)"
    )
    
    return parser.parse_args()


def main():
    """Run the OAuth token generator."""
    args = parse_args()
    
    # Get credentials from arguments or environment
    consumer_key = args.consumer_key or os.environ.get("TRIPIT_CONSUMER_KEY")
    consumer_secret = args.consumer_secret or os.environ.get("TRIPIT_CONSUMER_SECRET")
    
    if not consumer_key or not consumer_secret:
        print("Error: Both consumer key and consumer secret are required")
        print("You can provide them as command-line arguments or environment variables:")
        print("  --consumer-key=YOUR_KEY or TRIPIT_CONSUMER_KEY environment variable")
        print("  --consumer-secret=YOUR_SECRET or TRIPIT_CONSUMER_SECRET environment variable")
        sys.exit(1)
    
    try:
        # Initialize the OAuth handler and get tokens
        oauth = TripItOAuth(consumer_key, consumer_secret)
        
        print("TripIt OAuth Token Generator")
        print("===========================")
        print("This tool will help you generate OAuth tokens for the TripIt API.")
        print("It will open a web browser for you to authorize the application.")
        print()
        
        # Run the full authorization flow
        access_token, access_token_secret = oauth.authorize_app()
        
        # Print instructions for using the tokens
        print("\nOAuth authorization successful!")
        print("===============================")
        print("To use these tokens in your application, add them to your .env file:")
        print(f"TRIPIT_OAUTH_TOKEN={access_token}")
        print(f"TRIPIT_OAUTH_TOKEN_SECRET={access_token_secret}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
