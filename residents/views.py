from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Resident
from .serializers import ResidentSerializer


class ResidentViewSet(viewsets.ModelViewSet):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["date_of_birth"]
    search_fields = ["name", "family_contact", "health_history"]
    ordering_fields = ["name", "date_of_birth", "created_at"]
    ordering = ["name"]
