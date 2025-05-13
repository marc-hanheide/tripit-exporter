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

## Usage

### Starting the server

#### Option 1: Running directly

```bash
# Start with default settings (host: 0.0.0.0, port: 8000)
python -m tripit_mcp

# Or with custom host and port
python -m tripit_mcp --host 127.0.0.1 --port 8080

# If the tripit-mcp command is in your PATH, you can also use:
# tripit-mcp
# tripit-mcp --host 127.0.0.1 --port 8080
```

If you get "command not found: tripit-mcp", it means the command is not in your PATH. This can happen depending on how Python and uv install script entry points on your system. Using the `python -m` approach above will always work.

#### Option 2: Using Docker Compose (recommended)

1. Copy the example environment file and fill in your TripIt API credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Build and start the container:
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
