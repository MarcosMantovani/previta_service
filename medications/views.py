from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Medication
from .serializers import MedicationSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.select_related("resident").all()
    serializer_class = MedicationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["resident", "is_active", "schedule_time"]
    search_fields = ["name", "dosage", "duration", "resident__name"]
    ordering_fields = ["name", "schedule_time", "created_at"]
    ordering = ["resident__name", "schedule_time"]
