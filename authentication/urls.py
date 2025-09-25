__all__ = [
    'authentication_router'
]


from rest_framework import routers

from .views import (AuthenticatedUserViewSet, TokenExchangeViewSet,
                    TokenObtainPairViewSet, TokenRefreshViewSet)

app_name = 'authentication'

authentication_router = routers.DefaultRouter()
authentication_router.register(r"token/obtain", TokenObtainPairViewSet, basename="token-obtain")
authentication_router.register(r"token/exchange", TokenExchangeViewSet, basename="token-exchange")
authentication_router.register(r"token/refresh", TokenRefreshViewSet, basename="token-refresh")
authentication_router.register(r"", AuthenticatedUserViewSet, basename="authenticated-user")

urlpatterns = authentication_router.urls