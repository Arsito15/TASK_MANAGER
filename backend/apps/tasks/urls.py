from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import TaskViewSet

app_name = "tasks"

task_router = SimpleRouter()
task_router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("projects/<int:project_id>/", include(task_router.urls)),
    path("", include(task_router.urls)),
]