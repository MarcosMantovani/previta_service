from rest_framework import serializers
from .models import AppointmentExam, ExamAttachment
from residents.serializers import ResidentSerializer


class ExamAttachmentSerializer(serializers.ModelSerializer):
    # Campos para leitura - objetos completos
    resident = ResidentSerializer(read_only=True)
    appointment_exam = serializers.SerializerMethodField()

    # Campos para escrita - apenas IDs
    resident_id = serializers.IntegerField(write_only=True)
    appointment_exam_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    # Campos adicionais read-only
    resident_name = serializers.CharField(source="resident.name", read_only=True)
    appointment_exam_description = serializers.CharField(
        source="appointment_exam.description", read_only=True
    )
    file_extension = serializers.ReadOnlyField()

    class Meta:
        model = ExamAttachment
        fields = [
            "id",
            "resident",
            "resident_id",
            "resident_name",
            "appointment_exam",
            "appointment_exam_id",
            "appointment_exam_description",
            "file",
            "description",
            "file_extension",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_appointment_exam(self, obj):
        if obj.appointment_exam:
            # Evitar import circular - retornar dados básicos do appointment_exam
            return {
                "id": obj.appointment_exam.id,
                "type": obj.appointment_exam.type,
                "description": obj.appointment_exam.description,
                "date_time": obj.appointment_exam.date_time,
                "status": obj.appointment_exam.status,
            }
        return None

    def create(self, validated_data):
        resident_id = validated_data.pop("resident_id")
        appointment_exam_id = validated_data.pop("appointment_exam_id", None)

        validated_data["resident_id"] = resident_id
        if appointment_exam_id is not None:
            validated_data["appointment_exam_id"] = appointment_exam_id

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "resident_id" in validated_data:
            resident_id = validated_data.pop("resident_id")
            validated_data["resident_id"] = resident_id

        if "appointment_exam_id" in validated_data:
            appointment_exam_id = validated_data.pop("appointment_exam_id")
            validated_data["appointment_exam_id"] = appointment_exam_id

        return super().update(instance, validated_data)


class AppointmentExamSerializer(serializers.ModelSerializer):
    # Campo para leitura - objeto completo
    resident = ResidentSerializer(read_only=True)

    # Campo para escrita - apenas ID
    resident_id = serializers.IntegerField(write_only=True)

    # Campos adicionais read-only
    is_overdue = serializers.ReadOnlyField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentExam
        fields = [
            "id",
            "resident",
            "resident_id",
            "attachments",
            "type",
            "type_display",
            "description",
            "date_time",
            "status",
            "status_display",
            "notes",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_attachments(self, obj):
        return ExamAttachmentSerializer(obj.attachments.all(), many=True).data

    def create(self, validated_data):
        resident_id = validated_data.pop("resident_id")
        validated_data["resident_id"] = resident_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "resident_id" in validated_data:
            resident_id = validated_data.pop("resident_id")
            validated_data["resident_id"] = resident_id
        return super().update(instance, validated_data)
