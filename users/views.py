from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import (
    assign_perm,
    get_objects_for_group,
    get_perms,
    remove_perm,
)
from rest_framework import filters, serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminUserOrStaff
from common.filters import UnaccentSearchFilter
from users.models import User
from users.serializers import (
    AddUserToGroupSerializer,
    ChangePasswordSerializer,
    GroupSerializer,
    UserSerializer,
    UserCreateSerializer,
)

__all__ = ["UserViewSet"]


class UserViewSet(ModelViewSet):
    """
    A viewset for managing users.

    This viewset provides CRUD operations for the User model.
    It allows users to create, read, update, and delete users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "id"

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação
        """
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100
    filter_backends = [
        DjangoFilterBackend,
        UnaccentSearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["groups", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = "__all__"
    ordering = ["first_name"]

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """
        Endpoint para alterar a senha do usuário autenticado
        """
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Senha alterada com sucesso."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserGroupViewSet(ModelViewSet):
    """
    A viewset for managing user groups.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_url_kwarg = "group_id"
    permission_classes = [IsAdminUserOrStaff]
    pagination_class = PageNumberPagination

    @action(detail=True, methods=["delete"], url_path="members/(?P<user_uuid>[^/.]+)")
    def remove_member(self, request, group_id=None, user_uuid=None):
        group = self.get_object()
        try:
            user = group.user_set.get(uuid=user_uuid)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário não encontrado no grupo."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group.user_set.remove(user)
        return Response(
            {"detail": "Usuário removido do grupo."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get", "post"], url_path="members")
    def get_or_create_members(self, request, group_id=None, user_uuid=None):
        group = self.get_object()
        if request.method == "GET":
            group_members = group.user_set.all()
            super_user = User.objects.filter(is_superuser=True)
            members = group_members.union(super_user)
            page = self.paginate_queryset(members)
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        elif request.method == "POST":
            serializer = AddUserToGroupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = serializer.validated_data["user"]
            group.user_set.add(user)

            return Response(
                {"detail": "Usuário adicionado ao grupo."}, status=status.HTTP_200_OK
            )

    @action(detail=True, methods=["get", "put"], url_path="permissions")
    def permissions(self, request, group_id=None):
        group = self.get_object()

        if request.method == "GET":
            results = []

            models_with_object_perms = [
                ("multiplex", "session"),
                ("multiplex", "channel"),
                ("organizations", "organization"),
                ("organizations", "department"),
                ("organizations", "team"),
                ("automation", "chatbot"),
            ]

            query = Q()
            for app_label, model in models_with_object_perms:
                query |= Q(app_label=app_label, model=model)

            content_types = ContentType.objects.filter(query)

            for ct in content_types:
                model_class = ct.model_class()
                if not model_class:
                    continue

                try:
                    objs = get_objects_for_group(
                        group, perms=[], klass=model_class, any_perm=True
                    )
                except Exception:
                    continue

                for obj in objs:
                    perms = get_perms(group, obj)
                    results.append(
                        {
                            "object_id": str(obj.pk),
                            "content_type": ct.model,
                            "app_label": ct.app_label,
                            "permissions": perms,
                        }
                    )

            page = self.paginate_queryset(results)
            return self.get_paginated_response(page)

        elif request.method == "PUT":

            class ObjectPermissionsSerializer(serializers.Serializer):
                permissions = serializers.ListField(
                    child=serializers.CharField(), allow_empty=True
                )
                object_app_label = serializers.CharField()
                object_model = serializers.CharField()
                object_uuid = serializers.UUIDField()

            class BulkSetPermissionsSerializer(serializers.Serializer):
                objects = serializers.ListField(child=ObjectPermissionsSerializer())

            serializer = BulkSetPermissionsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Modelos para checar
            models_with_object_perms = [
                ("multiplex", "session"),
                ("multiplex", "channel"),
                ("organizations", "organization"),
                ("organizations", "department"),
                ("organizations", "team"),
                ("automation", "chatbot"),
            ]

            # 1. Mapear todos os ContentTypes usados
            content_types = {
                (ct.app_label, ct.model): ct
                for ct in ContentType.objects.filter(
                    Q(app_label__in=set(m[0] for m in models_with_object_perms)),
                    Q(model__in=set(m[1] for m in models_with_object_perms)),
                )
            }

            # 2. Obter TODOS os objetos que o grupo tem permissão atualmente (para os modelos listados)
            existing_objects = []
            for app_label, model in models_with_object_perms:
                ct = content_types.get((app_label, model))
                if not ct:
                    continue
                model_class = ct.model_class()
                if not model_class:
                    continue
                try:
                    objs = get_objects_for_group(
                        group, perms=[], klass=model_class, any_perm=True
                    )
                    for o in objs:
                        existing_objects.append(
                            {
                                "app_label": app_label,
                                "model": model,
                                "id": str(getattr(o, "id", o.pk)),
                                "object": o,
                            }
                        )
                except Exception:
                    continue

            # 3. Criar sets para facilitar buscas
            existing_set = set(
                (eo["app_label"], eo["model"], eo["id"]) for eo in existing_objects
            )
            incoming_set = set(
                (obj["object_app_label"], obj["object_model"], str(obj["object_id"]))
                for obj in data["objects"]
            )

            # 4. Objetos para remover permissões: que existem mas não vieram no POST
            to_remove = existing_set - incoming_set

            # 5. Remover permissões para objetos não enviados
            for app_label, model, id in to_remove:
                ct = content_types.get((app_label, model))
                if not ct:
                    continue
                obj = ct.get_object_for_this_type(id=id)
                perms = get_perms(group, obj)
                for perm in perms:
                    remove_perm(perm, group, obj)

            # 6. Atualizar permissões para objetos enviados
            results = []
            for obj_data in data["objects"]:
                app_label = obj_data["object_app_label"]
                model = obj_data["object_model"]
                uuid = str(obj_data["object_uuid"])
                new_perms = set(obj_data["permissions"])

                ct = content_types.get((app_label, model))
                if not ct:
                    continue
                model_class = ct.model_class()
                try:
                    obj = model_class.objects.get(uuid=uuid)
                except model_class.DoesNotExist:
                    return Response(
                        {
                            "detail": f"Objeto {app_label}.{model}:{uuid} não encontrado."
                        },
                        status=404,
                    )

                current_perms = set(get_perms(group, obj))

                for perm in current_perms - new_perms:
                    remove_perm(perm, group, obj)
                for perm in new_perms - current_perms:
                    assign_perm(perm, group, obj)

                results.append(
                    {
                        "object": f"{app_label}.{model}:{uuid}",
                        "permissions_set": list(new_perms),
                    }
                )

            return Response(
                {
                    "detail": "Permissões do grupo atualizadas com sucesso.",
                    "updated": results,
                    "removed_objects_count": len(to_remove),
                }
            )

        return Response(status=405)
