from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "appointments"

router = DefaultRouter()
router.register(r"appointments", views.AppointmentExamViewSet)
router.register(r"attachments", views.ExamAttachmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
