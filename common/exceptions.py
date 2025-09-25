from rest_framework.exceptions import APIException
from rest_framework import status


class NotImplementedAPIException(APIException):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    default_detail = 'Esta funcionalidade ainda não foi implementada.'
    default_code = 'not_implemented'