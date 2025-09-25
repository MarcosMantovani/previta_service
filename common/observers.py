from functools import partial
from typing import Type, Optional

from django.db.models import Model
from rest_framework.serializers import Serializer

from djangochannelsrestframework.observer.model_observer import ModelObserver


def overridable_model_observer(
    model: Type[Model],
    observer_class: Type[ModelObserver] = ModelObserver,
    serializer_class: Optional[Type[Serializer]] = None,
    many_to_many: bool = False,
    **kwargs
):
    """
    A custom implementation of model_observer decorator that allows to use a custom observer class
    Original implementation:
        from djangochannelsrestframework.observer import model_observer
    For reference:
        https://raw.githubusercontent.com/NilCoalescing/djangochannelsrestframework/refs/heads/master/djangochannelsrestframework/observer/__init__.py
    """
    return partial(
        observer_class,
        model_cls=model,
        serializer_class=serializer_class,
        many_to_many=many_to_many,
        **kwargs
    )