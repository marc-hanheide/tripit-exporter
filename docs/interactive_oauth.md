# Interactive OAuth Login for TripIt MCP

This document provides a detailed guide on how to use the interactive OAuth login feature in the TripIt MCP server.

## Overview

The TripIt MCP server now includes a dedicated OAuth authentication flow that can be used directly through the Model Context Protocol (MCP) interface. This feature allows users to authenticate with TripIt without needing to pre-generate and configure OAuth tokens as environment variables.

## Authentication Flow

The interactive OAuth process follows these steps:

1. Client calls `tripit_login` tool to initiate the OAuth flow
2. Server returns an authorization URL and instructions
3. User opens the URL in a browser and authorizes the application
4. Client calls `tripit_login_complete` tool with the request token from step 1
5. Server exchanges the token for access tokens and stores them internally
6. All subsequent API calls use the stored tokens

## MCP Tools for Authentication

### `tripit_login`

Initiates the OAuth authentication process.

**Input:** None

**Output:**
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

Completes the OAuth authentication process after user authorization.

**Input:**
- `request_token`: The request token from the previous step
- `request_token_secret`: The request token secret from the previous step

**Output on success:**
```json
{
  "status": "authenticated",
  "message": "Successfully authenticated with TripIt",
  "authenticated": true
}
```

**Output on failure:**
```json
{
  "status": "error",
  "error": "Error message details",
  "authenticated": false
}
```

### `tripit_auth_status`

Checks the current authentication status.

**Input:** None

**Output when authenticated:**
```json
{
  "authenticated": true,
  "message": "You are authenticated with TripIt API"
}
```

**Output when not authenticated:**
```json
{
  "authenticated": false,
  "message": "You are not authenticated with TripIt API",
  "instructions": "Please call tripit_login to authenticate"
}
```

## Example Usage

### Python Example

```python
# 1. Call tripit_login to start the process
login_response = client.call("tripit_login")

# 2. Extract token information and authorization URL
request_token = login_response["request_token"]
request_token_secret = login_response["request_token_secret"]
auth_url = [i for i in login_response["instructions"] if i.startswith("http")][0]

# 3. Prompt user to visit the URL and authorize access
print(f"Please visit {auth_url} and authorize the application")
input("Press Enter when done...")

# 4. Complete the authentication process
complete_response = client.call(
    "tripit_login_complete",
    request_token=request_token,
    request_token_secret=request_token_secret
)

# 5. Check if authentication was successful
if complete_response["authenticated"]:
    print("Successfully authenticated!")
    
    # 6. Now you can use other TripIt API endpoints
    trips_response = client.call("list_trips")
```

## Benefits of Interactive Login

1. **No Environment Variables Required**: Users don't need to set OAuth tokens in environment variables
2. **Simplified Integration**: OAuth flow handled directly through the MCP interface
3. **Better Security**: Tokens are stored in-memory and not exposed to the client
4. **Consistent User Experience**: Provides a familiar OAuth authorization flow

## Important Notes

1. Authentication status is maintained only for the current session
2. If the server restarts, authentication will need to be performed again
3. Multiple clients can use the same server instance with the same authentication
4. For production deployments, using environment variables remains an option

See the example script at `examples/interactive_login.py` for a complete demonstration of the interactive OAuth flow.
