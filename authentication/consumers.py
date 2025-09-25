import logging

from django.utils.translation import gettext_lazy as _
from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (TokenObtainPairSerializer,
                                                  TokenRefreshSerializer)
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

class JWTTokenConsumer(GenericAsyncAPIConsumer):

    @action()
    def validate(self, action=None, request_id=None, data=None, **kwargs):
        
        try: 
            AccessToken(data.get("access_token"))
            return {
                "action": action,
                "errors": [],
                "response_status": 200,
                "request_id": request_id,
                "data": {
                    "valid": True
                }
            }, 200            
        except:
            return {
                "action": action,
                "errors": [],
                "response_status": 200,
                "request_id": request_id,
                "data": {
                    "valid": False
                }
            }, 200


    @action()
    def obtain(self, action=None, request_id=None, data=None, **kwargs):

        serializer = TokenObtainPairSerializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
            return {
                "action": action,
                "errors": [],
                "response_status": 200,
                "request_id": request_id,
                "data": serializer.validated_data
            }, 200
        
        except TokenError as e:
            return {
                "action": action,
                "errors": [
                    {
                        "message": str(_('Incorrect authentication credentials.')),
                        "code": "authentication_failed"
                    }
                ],''
                "response_status": 401,
                "request_id": request_id,
            }, 200

    @action()
    def refresh(self, action=None, request_id=None, data=None, **kwargs):
        serializer = TokenRefreshSerializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
            return {
                "action": action,
                "errors": [],
                "response_status": 200,
                "request_id": request_id,
                "data": serializer.validated_data
            }, 200
        except TokenError as e:
            return {
                "action": action,
                "errors": [
                    {
                        "message": str(_('Incorrect authentication credentials.')),
                        "code": "authentication_failed"
                    }
                ],
                "response_status": 401,
                "request_id": request_id
            }, 200
