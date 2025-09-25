from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, UserGroupViewSet

app_name = 'users'

__all__ = [
    'users_router'
]

users_router = DefaultRouter()
users_router.register(r"users", UserViewSet, basename='user')
users_router.register(r"groups", UserGroupViewSet, basename='user-group')

urlpatterns = [
    path('', include(users_router.urls)),
]