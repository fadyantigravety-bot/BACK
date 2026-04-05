import urllib.parse
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        # Verify and decode the token
        UntypedToken(token_key)
        
        # We need to manually decode to get the user ID
        import jwt
        from django.conf import settings
        decoded_data = jwt.decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        
        user_id = decoded_data.get('user_id')
        if not user_id:
            return AnonymousUser()
            
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist, Exception):
        return AnonymousUser()

class TokenAuthMiddleware:
    """
    Custom middleware that extracts the JWT token from the query string and authenticates the user.
    Usage: wss://example.com/ws/chat/123/?token=<jwt_token>
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = urllib.parse.parse_qs(query_string)
        
        token = query_params.get('token', [None])[0]
        
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
            
        return await self.inner(scope, receive, send)

def TokenAuthMiddlewareStack(inner):
    """Factory function for applying our custom token auth middleware."""
    from channels.sessions import CookieMiddleware
    from channels.sessions import SessionMiddleware
    
    return CookieMiddleware(SessionMiddleware(TokenAuthMiddleware(inner)))
