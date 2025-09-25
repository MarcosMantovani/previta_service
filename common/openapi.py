from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers


class DummySerializer(serializers.Serializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance):
        return instance

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ValidationErrorSerializer(DummySerializer):
    errors = serializers.DictField(child=serializers.ListSerializer(child=serializers.CharField()))
    non_field_errors = serializers.ListSerializer(child=serializers.CharField())


class GenericErrorSerializer(DummySerializer):
    detail = serializers.CharField()


class UnauthenticatedErrorSerializer(GenericErrorSerializer):
    pass


class ForbiddenErrorSerializer(GenericErrorSerializer):
    pass


class NotFoundErrorSerializer(GenericErrorSerializer):
    pass


class BotAutoSchema(AutoSchema):
    def _get_response_bodies(self):
        response_bodies = super()._get_response_bodies()
        if len(list(filter(lambda _:_.startswith('4'), response_bodies.keys()))):
            return response_bodies

        add_error_codes = []
        add_error_codes.append('400')

        if self.get_auth():
            add_error_codes.append('401')
            add_error_codes.append('403')

        if not (self.method == 'GET' and self._is_list_view()):
            if len(list(filter(lambda _: _['in'] == 'path', self._get_parameters()))):
                add_error_codes.append('404')

        self.error_response_bodies = {
            '400': self._get_response_for_code(ValidationErrorSerializer, '400'),
            '401': self._get_response_for_code(UnauthenticatedErrorSerializer, '401'),
            '403': self._get_response_for_code(ForbiddenErrorSerializer, '403'),
            '404': self._get_response_for_code(NotFoundErrorSerializer, '404')
            }
        for code in add_error_codes:
            response_bodies[code] = self.error_response_bodies[code]
        return response_bodies