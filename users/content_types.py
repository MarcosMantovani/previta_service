from django.contrib.contenttypes.models import ContentType
from django.apps import apps

_content_type_cache = {}


def get_user_content_type():
    model = apps.get_model("users", "User")

    if "user" not in _content_type_cache:
        try:
            _content_type_cache["user"] = ContentType.objects.get_for_model(model)
        except Exception:
            _content_type_cache["user"] = None
    return _content_type_cache["user"]
