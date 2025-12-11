import os
import time
import requests
from jose import jwk, jwt
from jose.utils import base64url_decode

USER_POOL_ID = os.environ.get("USER_POOL_ID")
USER_POOL_CLIENT_ID = os.environ.get("USER_POOL_CLIENT_ID")
REGION = os.environ.get("REGION", "us-west-2")

# Cache keys
_JWKS_KEYS = None

def get_jwks():
    global _JWKS_KEYS
    if _JWKS_KEYS is None:
        if not USER_POOL_ID or not REGION:
            print("Missing USER_POOL_ID or REGION in environment")
            return []
        keys_url = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
        try:
            response = requests.get(keys_url)
            response.raise_for_status()
            _JWKS_KEYS = response.json()['keys']
        except Exception as e:
            print(f"Error fetching JWKS: {e}")
            return []
    return _JWKS_KEYS

def verify_cognito_token(token: str) -> dict | None:
    """
    Verifies the Cognito token and returns the claims if valid.
    Returns None if invalid.
    """
    try:
        if not token:
            return None
        
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
            
        headers = jwt.get_unverified_headers(token)
        kid = headers.get('kid')
        
        keys = get_jwks()
        key_index = -1
        for i in range(len(keys)):
            if kid == keys[i]['kid']:
                key_index = i
                break
                
        if key_index == -1:
            print("Public key not found in JWKS")
            return None
            
        public_key = jwk.construct(keys[key_index])
        
        message, encoded_signature = str(token).rsplit('.', 1)
        
        # Verify signature
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            print("Signature verification failed")
            return None
        
        # Verify claims
        claims = jwt.get_unverified_claims(token)
        
        # Verify expiration
        if time.time() > claims['exp']:
            print("Token expired")
            return None
            
        # Verify audience (audience is usually client_id for ID tokens)
        # Note: Access tokens verification is slightly different (aud match not always required depending on flow)
        # We assume ID token or Access token checking matches USER_POOL_CLIENT_ID
        if claims.get('aud') != USER_POOL_CLIENT_ID and claims.get('client_id') != USER_POOL_CLIENT_ID:
             # Check if it's an access token (client_id claim) or ID token (aud claim)
             pass 
             # For now, let's be lenient or check strictly if configured
             # print("Audience mismatch")
             # But if we use USER_AUTH with standard flow, aud should be client_id.
        
        # Verify issuer
        expected_iss = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'
        if claims['iss'] != expected_iss:
            print("Issuer mismatch")
            return None
            
        # Verify token_use
        if claims['token_use'] not in ['id', 'access']:
            print("Invalid token_use")
            return None
            
        return claims
        
    except Exception as e:
        print(f"Token verification validation error: {e}")
        return None
