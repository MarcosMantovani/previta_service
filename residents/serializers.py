from rest_framework import serializers
from .models import Resident


class ResidentSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()

    class Meta:
        model = Resident
        fields = [
            "id",
            "name",
            "date_of_birth",
            "age",
            "family_contact",
            "health_history",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
