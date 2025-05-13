# TripIt OAuth Troubleshooting Guide

## Summary of OAuth Issues and Fixes

After analyzing the code and implementation of TripIt OAuth authentication, several potential issues were identified and fixed:

1. **Parameter Encoding**: Strict RFC 3986 encoding for all OAuth parameters in the signature base string
2. **OAuth Callback Handling**: Including the `oauth_callback` parameter in both the Authorization header and URL query parameters
3. **Signature Key Formation**: Ensuring proper encoding and concatenation of the consumer secret and token secret
4. **Header Formatting**: Proper comma separation and parameter quoting in the Authorization header
5. **Content-Type Headers**: Adding `Content-Type: application/x-www-form-urlencoded` header

## How to Fix TripIt OAuth Authentication

Two fixed implementations are provided:

### Option 1: Use the standalone script for OAuth token generation

The `fixed_oauth.py` script is a standalone solution that uses the `requests` library for OAuth token generation. This script:

1. Handles the full OAuth 1.0a flow with TripIt
2. Provides detailed logs for debugging
3. Tests generated tokens with a real API call

**Usage:**
```bash
# Make sure requests is installed
pip install requests

# Set your TripIt API credentials as environment variables (optional)
export TRIPIT_CONSUMER_KEY="your_consumer_key"
export TRIPIT_CONSUMER_SECRET="your_consumer_secret"

# Run the script
python scripts/fixed_oauth.py
```

### Option 2: Use the updated OAuth module

The `oauth_fixed.py` file provides an updated implementation of the `TripItOAuth` class with all the fixes applied. To use this implementation:

1. Replace the current `oauth.py` with `oauth_fixed.py`, or
2. Import and use the fixed version directly:

```python
from tripit_mcp.oauth_fixed import TripItOAuth

oauth = TripItOAuth(consumer_key, consumer_secret)
access_token, access_token_secret = oauth.authorize_app()
```

## OAuth Fixed Implementation Details

The key improvements in the fixed implementation include:

### 1. RFC 3986 Parameter Encoding

```python
# Proper encoding for signature base string
param_pairs = []
for k, v in sorted(params.items()):
    k_enc = quote(str(k), safe='')
    v_enc = quote(str(v) if v is not None else '', safe='')
    param_pairs.append(f"{k_enc}={v_enc}")

param_string = '&'.join(param_pairs)
```

### 2. Consistent OAuth Callback Handling

```python
# OAuth parameters with callback
oauth_params = {
    'oauth_consumer_key': consumer_key,
    'oauth_nonce': generate_nonce(),
    'oauth_signature_method': 'HMAC-SHA1',
    'oauth_timestamp': str(int(time.time())),
    'oauth_version': '1.0',
    'oauth_callback': 'oob'  # Required for OAuth 1.0a
}

# Also include in URL parameters for maximum compatibility
params = {'oauth_callback': 'oob'}
response = requests.get(REQUEST_TOKEN_URL, headers=headers, params=params, auth=auth)
```

### 3. Improved Authorization Header Formation

```python
auth_header_parts = []
for k, v in sorted(oauth_params.items()):
    auth_header_parts.append(f'{quote(k, safe="")}="{quote(v, safe="~")}"')

auth_header = 'OAuth ' + ', '.join(auth_header_parts)
```

## Debugging the OAuth Process

If issues persist, use the `scripts/debug_oauth.py` script to see detailed information about the request and response for each step of the OAuth process.

If you need further assistance with TripIt API authentication, please review TripIt's official API documentation or contact their developer support.
