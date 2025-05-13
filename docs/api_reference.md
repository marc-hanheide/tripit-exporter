# TripIt MCP API Reference

This document provides a comprehensive reference for all the Model Context Protocol (MCP) functions available in the TripIt MCP Server.

## Authentication Functions

These functions handle the authentication process with TripIt.

### `tripit_login`

Initiates the OAuth authentication process with TripIt.

**Request:**
```json
{
  "function": "tripit_login",
  "arguments": {}
}
```

**Response:**
```json
{
  "status": "authorization_needed",
  "message": "Please authorize access to your TripIt account",
  "instructions": [
    "1. Go to the following URL in your browser:",
    "https://www.tripit.com/oauth/authorize?oauth_token=REQUEST_TOKEN&oauth_callback=oob",
    "2. Log in to TripIt (if needed) and authorize the application",
    "3. Once authorized, return here and call tripit_login_complete"
  ],
  "request_token": "REQUEST_TOKEN",
  "request_token_secret": "REQUEST_TOKEN_SECRET"
}
```

### `tripit_login_complete`

Completes the OAuth authentication process after the user has authorized access.

**Request:**
```json
{
  "function": "tripit_login_complete",
  "arguments": {
    "request_token": "REQUEST_TOKEN",
    "request_token_secret": "REQUEST_TOKEN_SECRET"
  }
}
```

**Response (Success):**
```json
{
  "status": "authenticated",
  "message": "Successfully authenticated with TripIt",
  "authenticated": true
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "Error message details",
  "authenticated": false
}
```

### `tripit_auth_status`

Checks if the user is currently authenticated with TripIt.

**Request:**
```json
{
  "function": "tripit_auth_status",
  "arguments": {}
}
```

**Response (Authenticated):**
```json
{
  "authenticated": true,
  "message": "You are authenticated with TripIt API and tokens are valid"
}
```

**Response (Not Authenticated):**
```json
{
  "authenticated": false,
  "message": "You are not authenticated with TripIt API",
  "instructions": "Please call tripit_login to authenticate"
}
```

## Trip Information Functions

These functions provide access to trip information from TripIt. All require prior authentication.

### `list_trips`

Lists all trips, optionally filtered by date range.

**Request:**
```json
{
  "function": "list_trips",
  "arguments": {
    "start_date": "2023-01-01",  // Optional
    "end_date": "2023-12-31"     // Optional
  }
}
```

**Response (Success):**
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
    // ... more trips
  ]
}
```

**Response (Error):**
```json
{
  "error": "Error message details"
}
```

**Response (Not Authenticated):**
```json
{
  "error": "OAuth authentication required. Please use the 'tripit_login' tool first."
}
```

### `get_trip`

Gets detailed information about a specific trip.

**Request:**
```json
{
  "function": "get_trip",
  "arguments": {
    "trip_id": "123456789"
  }
}
```

**Response (Success):**
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
    "TripInvitees": [...],
    "Activities": [...],
    "Notes": [...],
    "Segments": [
      {
        "id": "12345",
        "segment_type_code": "AIR",
        "StartDateTime": {...},
        "EndDateTime": {...},
        // ... more segment details
      },
      // ... more segments
    ]
    // ... more trip data
  }
}
```

**Response (Error):**
```json
{
  "error": "Error message details"
}
```

**Response (Not Authenticated):**
```json
{
  "error": "OAuth authentication required. Please use the 'tripit_login' tool first."
}
```

## Authentication Flow Example

Here's an example of the complete authentication flow:

1. Check authentication status:
```json
{"function": "tripit_auth_status", "arguments": {}}
```

2. If not authenticated, start the OAuth process:
```json
{"function": "tripit_login", "arguments": {}}
```

3. User visits the URL in a browser and authorizes access

4. Complete the authentication:
```json
{
  "function": "tripit_login_complete",
  "arguments": {
    "request_token": "REQUEST_TOKEN",
    "request_token_secret": "REQUEST_TOKEN_SECRET"
  }
}
```

5. Now you can access trip information:
```json
{"function": "list_trips", "arguments": {}}
```

## Error Handling

Most functions will return an "error" field in the response if something goes wrong. Common errors include:

- Authentication errors (missing or invalid tokens)
- API rate limiting
- Network connectivity issues
- Invalid input parameters

Always check for the presence of an "error" field in responses and handle it appropriately.
