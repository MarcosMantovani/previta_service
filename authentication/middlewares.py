from pprint import pp
import pprint
import logging
from urllib.parse import parse_qs
from functools import lru_cache
import time

from channels.auth import AuthMiddlewareStack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

# Cache for user lookups to reduce database queries
_user_cache = {}
_cache_timeout = 300  # 5 minutes


@database_sync_to_async
def get_user(user_id):
    try:
        # Check cache first
        cache_key = f"user_{user_id}"
        current_time = time.time()
        
        if cache_key in _user_cache:
            cached_user, cache_time = _user_cache[cache_key]
            if current_time - cache_time < _cache_timeout:
                return cached_user
        
        # Cache miss or expired, fetch from database
        user = get_user_model().objects.get(id=user_id)
        _user_cache[cache_key] = (user, current_time)
        
        # Clean old cache entries (keep cache size manageable)
        if len(_user_cache) > 1000:
            expired_keys = [
                key for key, (_, cache_time) in _user_cache.items()
                if current_time - cache_time >= _cache_timeout
            ]
            for key in expired_keys:
                _user_cache.pop(key, None)
        
        return user
    except get_user_model().DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):

        close_old_connections()

        headers = dict(scope.get('headers', {}))
        
        # Handle origin header safely
        origin = headers.get(b'origin')
        if origin:
            origin_str = origin.decode('utf-8')
            scope['origin'] = origin_str
            
            # Extract hostname safely
            try:
                if '//' in origin_str:
                    # Format: http://hostname:port or https://hostname:port
                    origin_hostname = origin_str.split('//')[1].split(':')[0]
                else:
                    # Format: hostname:port or just hostname
                    origin_hostname = origin_str.split(':')[0]
                scope['origin_hostname'] = origin_hostname
            except (IndexError, ValueError):
                # If parsing fails, use the original value
                scope['origin_hostname'] = origin_str
                logger.warning(f"Could not parse origin hostname from: {origin_str}")

        try:
            # Get the token from query string
            query_string = scope.get("query_string", b"").decode("utf8")
            token = parse_qs(query_string).get("token")
            
            if token and token[0]:
                token_value = token[0]
                try:
                    # Validate the token
                    access_token = AccessToken(token_value)
                    logger.info(f"Token validated successfully")
                    
                    decoded_data = jwt_decode(
                        token_value, settings.SECRET_KEY, algorithms=["HS256"])
                    
                    scope['user'] = await get_user(decoded_data.get("user_id"))
                    logger.info(f"User set in scope: {scope['user']}")
                    
                except (InvalidToken, TokenError) as e:
                    logger.error(f"Token validation failed: {e}")
                    scope['user'] = AnonymousUser()
            else:
                logger.info("No token found in query string")
                scope['user'] = AnonymousUser()

        except Exception as e:
            logger.error(f"Exception in token middleware: {e}")
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)


def TokenAuthMiddlewareStack(inner): 
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
