from django.db.models import Model
from djangochannelsrestframework import permissions
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import (CreateModelMixin,
                                                PatchModelMixin,
                                                UpdateModelMixin)
from djangochannelsrestframework.observer.generics import \
    ObserverModelInstanceMixin

from . import models, serializers


class LoggedUserConsumer(
    PatchModelMixin,
    UpdateModelMixin,
    ObserverModelInstanceMixin,
    GenericAsyncAPIConsumer,
):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, **kwargs) -> Model:
        return models.User.objects.filter(id=self.scope["user"].id).first()
