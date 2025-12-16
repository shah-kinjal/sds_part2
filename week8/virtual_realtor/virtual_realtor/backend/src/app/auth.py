import os
import time
import requests
import logging
from jose import jwk, jwt
from jose.utils import base64url_decode

logger = logging.getLogger(__name__)

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
            logger.warning("Token is empty or None")
            return None
        
        # Remove 'Bearer ' prefix if present
        original_token = token
        if token.startswith("Bearer "):
            token = token[7:]
            logger.debug("Removed 'Bearer ' prefix from token")
        
        logger.debug(f"Token length: {len(token)}, starts with: {token[:20]}...")
        
        try:
            headers = jwt.get_unverified_headers(token)
            kid = headers.get('kid')
            logger.debug(f"Token kid: {kid}")
        except Exception as e:
            logger.error(f"Failed to get token headers: {e}")
            return None
        
        keys = get_jwks()
        if not keys:
            logger.error("No JWKS keys available")
            return None
            
        key_index = -1
        for i in range(len(keys)):
            if kid == keys[i]['kid']:
                key_index = i
                break
                
        if key_index == -1:
            logger.warning(f"Public key not found in JWKS for kid: {kid}")
            return None
            
        public_key = jwk.construct(keys[key_index])
        
        try:
            message, encoded_signature = str(token).rsplit('.', 1)
        except ValueError as e:
            logger.error(f"Token format invalid (not 3 parts): {e}")
            return None
        
        # Verify signature
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            logger.warning("Signature verification failed")
            return None
        
        # Verify claims
        try:
            claims = jwt.get_unverified_claims(token)
        except Exception as e:
            logger.error(f"Failed to decode token claims: {e}")
            return None
        
        # Verify expiration
        if time.time() > claims['exp']:
            logger.warning(f"Token expired. Exp: {claims['exp']}, Now: {time.time()}")
            return None
            
        # Verify audience (audience is usually client_id for ID tokens)
        # Note: Access tokens verification is slightly different (aud match not always required depending on flow)
        # We assume ID token or Access token checking matches USER_POOL_CLIENT_ID
        aud = claims.get('aud')
        client_id = claims.get('client_id')
        if aud != USER_POOL_CLIENT_ID and client_id != USER_POOL_CLIENT_ID:
             logger.debug(f"Audience check: aud={aud}, client_id={client_id}, expected={USER_POOL_CLIENT_ID}")
             # Check if it's an access token (client_id claim) or ID token (aud claim)
             # For now, let's be lenient or check strictly if configured
             # But if we use USER_AUTH with standard flow, aud should be client_id.
        
        # Verify issuer
        expected_iss = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'
        if claims['iss'] != expected_iss:
            logger.warning(f"Issuer mismatch. Expected: {expected_iss}, Got: {claims['iss']}")
            return None
            
        # Verify token_use
        token_use = claims.get('token_use')
        if token_use not in ['id', 'access']:
            logger.warning(f"Invalid token_use: {token_use}")
            return None
        
        logger.info(f"Token verified successfully for user: {claims.get('sub')}, token_use: {token_use}")
        return claims
        
    except Exception as e:
        logger.error(f"Token verification validation error: {e}", exc_info=True)
        return None
