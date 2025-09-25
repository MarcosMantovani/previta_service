from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from . import models


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField(
        required=False, help_text="UUID do usuário", allow_null=True
    )

    permissions = PermissionSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = models.User
        exclude = ["password", "user_permissions", "polymorphic_ctype"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de usuários com senha
    """

    password = serializers.CharField(
        write_only=True, required=True, help_text="Senha do usuário"
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True, help_text="Confirmação da senha"
    )

    class Meta:
        model = models.User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "confirm_password",
            "is_active",
            "is_staff",
        ]
        extra_kwargs = {
            "is_staff": {"default": False},
            "is_active": {"default": True},
        }

    def validate_password(self, value):
        """
        Valida a senha usando os validadores do Django
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        """
        Valida se as senhas coincidem
        """
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "As senhas não coincidem."}
            )
        return data

    def create(self, validated_data):
        """
        Cria um novo usuário com senha criptografada
        """
        # Remove confirm_password pois não é campo do model
        validated_data.pop("confirm_password", None)

        # Usa o método create_user para criptografar a senha
        password = validated_data.pop("password")
        user = models.User.objects.create_user(password=password, **validated_data)
        return user


class AddUserToGroupSerializer(serializers.Serializer):
    user_id = serializers.SlugRelatedField(
        source="user",
        queryset=models.User.objects.all(),
        slug_field="id",
        required=True,
    )


class AssignPermissionSerializer(serializers.Serializer):
    permission = (
        serializers.CharField()
    )  # TODO: verificar se é melhor fazer por id de Permission model
    object_app_label = serializers.CharField()
    object_model = serializers.CharField()
    object_uuid = serializers.UUIDField()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para alteração de senha do usuário
    """

    new_password = serializers.CharField(required=True, help_text="Nova senha")
    confirm_password = serializers.CharField(
        required=True, help_text="Confirmação da nova senha"
    )

    def validate_new_password(self, value):
        """
        Valida a nova senha usando os validadores do Django
        """
        user = self.context["request"].user
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        """
        Valida se as senhas coincidem
        """
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "As senhas não coincidem."}
            )

        return data

    def save(self):
        """
        Altera a senha do usuário
        """
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
