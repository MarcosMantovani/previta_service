from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "medications"

router = DefaultRouter()
router.register(r"medications", views.MedicationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
