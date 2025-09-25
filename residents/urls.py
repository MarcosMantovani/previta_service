from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "residents"

router = DefaultRouter()
router.register(r"residents", views.ResidentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
