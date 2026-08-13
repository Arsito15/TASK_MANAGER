from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import ProjectViewSet

app_name = "projects"

project_router = SimpleRouter()
project_router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("organizations/<slug:org_slug>/", include(project_router.urls)),
    path("", include(project_router.urls)),
]