from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AppointmentExam, ExamAttachment
from .serializers import AppointmentExamSerializer, ExamAttachmentSerializer
from .filters import AppointmentExamFilter, ExamAttachmentFilter


class AppointmentExamViewSet(viewsets.ModelViewSet):
    queryset = AppointmentExam.objects.select_related("resident").all()
    serializer_class = AppointmentExamSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AppointmentExamFilter
    search_fields = ["description", "notes", "resident__name"]
    ordering_fields = ["date_time", "created_at"]
    ordering = ["-date_time"]

    def get_queryset(self):
        queryset = super().get_queryset()

        status_not = self.request.query_params.get("status_not")
        if status_not:
            status_not = status_not.split(",")
            queryset = queryset.exclude(status__in=status_not)

        return queryset


class ExamAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ExamAttachment.objects.select_related(
        "resident", "appointment_exam"
    ).all()
    serializer_class = ExamAttachmentSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ExamAttachmentFilter
    search_fields = ["description", "resident__name"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
