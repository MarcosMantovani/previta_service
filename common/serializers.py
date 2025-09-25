from rest_framework import serializers
from users.models import User
from users.serializers import UserSerializer
from .models import Note
from channels_redis.serializers import BaseMessageSerializer
import orjson
from channels_redis.serializers import registry


class CrossUserContextSerializer(serializers.Serializer):
    def get_user(self) -> User | None:
        if "request" in self.context and hasattr(self.context["request"], "user"):
            return self.context["request"].user
        elif "scope" in self.context and isinstance(self.context["scope"], dict):
            return self.context["scope"].get("user")
        return None


class JSONSerializer(BaseMessageSerializer):
    def as_bytes(self, message, *args, **kwargs):
        message = orjson.dumps(message, *args, **kwargs)
        return message

    from_bytes = staticmethod(orjson.loads)


registry.register_serializer("json", JSONSerializer)


class NoteSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Note
        fields = ["uuid", "contents", "author", "created_at", "updated_at"]
