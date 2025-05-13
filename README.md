# TripIt MCP Server

A Model Context Protocol (MCP) server that provides access to your TripIt trip data through a standardized interface. This server allows AI assistants and other MCP clients to fetch your past and upcoming trips from your TripIt account.

## Features

- Access your TripIt trips through MCP protocol
- List all trips with optional date range filtering
- Get detailed information about specific trips
- OAuth authenticated access to the TripIt API
- Built using FastMCP for MCP protocol implementation
- Docker and Docker Compose support for easy deployment

## Prerequisites

- Python 3.8+ (for local installation)
- [uv](https://github.com/astral-sh/uv) - Python package manager (for local installation)
- Docker and Docker Compose (for containerized deployment)
- TripIt account with API access (Consumer Key and Secret)
- OAuth token credentials (for authenticated access)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/tripit-mcp.git
cd tripit-mcp
```

### 2. Create and activate a virtual environment using uv

```bash
uv venv
source .venv/bin/activate  # On macOS/Linux
# Or on Windows: .venv\Scripts\activate
```

### 3. Install using uv

```bash
uv pip install -e .
```

This will install the package in development mode with all required dependencies.

## Configuration

### TripIt API Authentication

This server supports both 2-legged and 3-legged OAuth authentication with the TripIt API:

1. **Two-legged OAuth**: Uses only the Consumer Key and Secret (basic access)
2. **Three-legged OAuth**: Uses Consumer Key/Secret and user OAuth tokens (full access)

#### Generating OAuth Tokens

For full access to a user's TripIt account, you'll need to generate OAuth tokens. The package includes several utility scripts to help with this process:

##### Option 1: Using the simplified OAuth script (Recommended)

```bash
# Set your TripIt API credentials as environment variables
export TRIPIT_CONSUMER_KEY=your_consumer_key
export TRIPIT_CONSUMER_SECRET=your_consumer_secret

# Run the script
./get_oauth_tokens.py
```

##### Option 2: Using the built-in OAuth module

```bash
# Using environmental variables for credentials
export TRIPIT_CONSUMER_KEY=your_consumer_key
export TRIPIT_CONSUMER_SECRET=your_consumer_secret
python -m tripit_mcp.oauth

# Or directly within Python
from tripit_mcp.oauth import TripItOAuth
oauth = TripItOAuth(consumer_key, consumer_secret)
access_token, access_token_secret = oauth.authorize_app()
```

Either script will:
1. Get a request token from TripIt
2. Open a browser window asking you to authorize the application
3. After authorization, exchange the request token for access tokens
4. Display the tokens to add to your environment variables
5. Optionally verify the tokens with a test API call

### Environment Variables

Set the following environment variables before running the server:

```bash
# Required
export TRIPIT_CONSUMER_KEY="your_consumer_key"
export TRIPIT_CONSUMER_SECRET="your_consumer_secret"

# Optional - For authenticated access
export TRIPIT_OAUTH_TOKEN="your_oauth_token"
export TRIPIT_OAUTH_TOKEN_SECRET="your_oauth_token_secret"
```

### Getting TripIt API Credentials

1. Register for a developer account at [TripIt for Developers](https://www.tripit.com/developer)
2. Create a new application to get your Consumer Key and Consumer Secret
3. For OAuth tokens, you'll need to implement the OAuth flow or use the TripIt API to generate tokens

## Documentation

- [Interactive OAuth Login](docs/interactive_oauth.md) - Detailed guide on using the interactive OAuth login feature
- [API Reference](docs/api_reference.md) - Complete reference for all MCP functions

## Usage

### Starting the server

#### Option 1: Running directly

The server supports two modes of operation:

##### STDIO Mode (Default)

STDIO mode is perfect for integrating with other tools as a subprocess:

```bash
# Make sure your virtual environment is activated, then run:
python -m tripit_mcp  # Runs in stdio mode by default

# Explicitly specify stdio mode
python -m tripit_mcp --mode stdio
```

In this mode, the server communicates through stdin/stdout using the MCP protocol.

##### HTTP Mode

HTTP mode provides a web server interface to access the MCP functions:

```bash
# Start in HTTP mode with default host/port (0.0.0.0:8000)
python -m tripit_mcp --mode http

# Customize host and port
python -m tripit_mcp --mode http --host 127.0.0.1 --port 8080
```

The server uses FastMCP v2, which provides a modern, asyncio-based implementation of the Model Context Protocol.

##### Interactive OAuth Authentication

You can also use an interactive OAuth authentication process directly through the MCP by using the `tripit_login` tool. This approach doesn't require you to set the OAuth tokens as environment variables:

1. Start the server with only your consumer key and secret set:
```bash
export TRIPIT_CONSUMER_KEY="your_consumer_key"
export TRIPIT_CONSUMER_SECRET="your_consumer_secret"
python -m tripit_mcp
```

2. Use the `tripit_login` tool in your MCP client to initiate the authentication process
3. Follow the instructions to authorize the application in your browser
4. Use the `tripit_login_complete` tool to finalize authentication
5. Once authenticated, you can use the other TripIt API tools

For a complete example of interactive OAuth authentication, see the `examples/interactive_login.py` script.

See [Interactive OAuth Documentation](docs/interactive_oauth.md) for detailed information about the authentication flow.

#### Option 2: Using Docker Compose (recommended)

1. Copy the example environment file and fill in your TripIt API credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Build and start the container (runs in HTTP mode):
```bash
docker-compose up -d
```

3. Check the logs:
```bash
docker-compose logs -f
```

4. Stop the container:
```bash
docker-compose down
```

### MCP Functions

The server provides the following MCP functions:

#### Authentication Tools

Before using any of the data retrieval tools, you must authenticate with TripIt using one of these methods:

1. Set `TRIPIT_OAUTH_TOKEN` and `TRIPIT_OAUTH_TOKEN_SECRET` as environment variables (pre-authenticated)
2. Use the interactive login process via the MCP tools below

##### `tripit_login`

Initiates the OAuth authorization process with TripIt.

**Parameters:**
- None

**Returns:**
- Authorization URL and instructions for the user
- Request token details to use with `tripit_login_complete`

##### `tripit_login_complete`

Completes the OAuth authorization process after the user has authorized access.

**Parameters:**
- `request_token`: The request token from `tripit_login`
- `request_token_secret`: The request token secret from `tripit_login`

##### `tripit_auth_status`

Checks if you're currently authenticated with TripIt.

**Parameters:**
- None

#### Data Retrieval Tools

These tools require prior authentication via `tripit_login` or environment variables.

#### `list_trips`

Lists all trips, optionally filtered by date range.

**Parameters:**
- `start_date` (optional): Start date for filtering trips (YYYY-MM-DD)
- `end_date` (optional): End date for filtering trips (YYYY-MM-DD)

**Example request:**
```json
{
  "function": "list_trips",
  "arguments": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }
}
```

**Example response:**
```json
{
  "trips": [
    {
      "id": "123456789",
      "name": "Business Trip to New York",
      "start_date": "2023-03-15",
      "end_date": "2023-03-20",
      "primary_location": "New York, NY",
      "is_private": false
    },
    {
      "id": "987654321",
      "name": "Vacation in Paris",
      "start_date": "2023-06-10",
      "end_date": "2023-06-17",
      "primary_location": "Paris, France",
      "is_private": true
    }
  ]
}
```

#### `get_trip`

Gets detailed information about a specific trip.

**Parameters:**
- `trip_id` (required): The TripIt trip ID

**Example request:**
```json
{
  "function": "get_trip",
  "arguments": {
    "trip_id": "123456789"
  }
}
```

**Example response:**
```json
{
  "trip": {
    "id": "123456789",
    "display_name": "Business Trip to New York",
    "start_date": "2023-03-15",
    "end_date": "2023-03-20",
    "primary_location": "New York, NY",
    "is_private": "false",
    "relative_url": "/trip/show/id/123456789",
    "trip_lemmas": ["business", "trip", "new", "york"],
    "AirObject": [...],
    "LodgingObject": [...],
    "ActivityObject": [...],
    "TransportObject": [...]
  }
}
```

## OAuth Troubleshooting

If you're experiencing issues with TripIt API authentication:

### Common OAuth Issues

1. **"Access Request Failed"** when opening the authorization URL:
   - This usually means there's an issue with the OAuth request token request
   - Make sure your consumer key and secret are correct
   - Try using the `fixed_oauth.py` script which has stricter RFC 3986 encoding

2. **"Invalid oauth_verifier"** errors:
   - TripIt uses 'oob' (out-of-band) for the OAuth callback
   - Make sure 'oauth_callback=oob' is included correctly in the request

3. **Empty or unexpected responses from TripIt API**:
   - Check that your API application is approved and active in TripIt
   - Verify network connectivity to api.tripit.com

### OAuth Debugging Tools

Several debugging tools are available to help diagnose OAuth issues:

1. **Standalone OAuth script**:
   ```bash
   ./get_oauth_tokens.py
   ```

2. **Debug OAuth utility** (shows detailed request/response information):
   ```bash
   python scripts/debug_oauth.py
   ```

3. **Alternative OAuth implementations** to isolate issues:
   - `scripts/alt_oauth.py` - Uses `requests` library instead of `httpx`
   - `scripts/minimal_oauth.py` - Uses only standard library modules

For a detailed explanation of the OAuth fixes implemented in this project, see the [OAUTH_FIX.md](OAUTH_FIX.md) document.

## Using with MCP Clients

This MCP server can be used with any MCP-compatible client, including:

- Large Language Models (LLMs) that support the MCP protocol
- MCP client libraries in various programming languages
- Applications that can connect to MCP servers

To connect, point your MCP client to the server URL:

```
http://your-server-address:8000
```

## Development

### Running tests

```bash
# Make sure your virtual environment is activated
uv pip install -e ".[dev]"
pytest
```

### Building the package

```bash
# Make sure your virtual environment is activated
uv pip build
```

## License

MIT License

## Acknowledgments

- [FastMCP](https://github.com/shishirkh/fast-mcp) library for MCP implementation
- [TripIt API](https://tripit.github.io/api/doc/v1/) for providing travel data access
