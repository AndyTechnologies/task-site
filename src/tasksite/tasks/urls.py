from django.urls import path

from .views import (
    TaskListView,
    TaskCreateView,
    TaskDetailView,
    TaskUpdateView,
    TaskAuthorManagementView,
    MarkdownPreviewView,
)

app_name = "tasks"

urlpatterns = [
    path("", TaskListView.as_view(), name="list"),
    path("new/", TaskCreateView.as_view(), name="new"),
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="edit"),
    path("<int:pk>/authors/", TaskAuthorManagementView.as_view(), name="authors"),
    path("preview/", MarkdownPreviewView.as_view(), name="preview"),
]