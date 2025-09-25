from rest_framework import serializers
from .models import Medication


class MedicationSerializer(serializers.ModelSerializer):
    # Campo para escrita - apenas ID
    resident_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Medication
        fields = [
            "id",
            "resident_id",
            "name",
            "dosage",
            "schedule_time",
            "duration",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        resident_id = validated_data.pop("resident_id")
        validated_data["resident_id"] = resident_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "resident_id" in validated_data:
            resident_id = validated_data.pop("resident_id")
            validated_data["resident_id"] = resident_id
        return super().update(instance, validated_data)
