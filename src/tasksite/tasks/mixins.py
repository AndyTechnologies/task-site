"""
Mixins de permisos para Tasks.

Centralizan la lógica de control de acceso a tareas.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Task


class TaskAccessMixin(LoginRequiredMixin):
    """
    Mixin que filtra el queryset a tareas accesibles por el usuario actual.

    Debe usarse en ListView, DetailView, UpdateView, etc.
    """

    def get_queryset(self):
        # Usar el manager del modelo para acceder a accessible_by
        return self.model.objects.accessible_by(self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Verificación adicional por si acaso
        if not obj.is_author(self.request.user):
            raise PermissionDenied("No tienes acceso a esta tarea.")
        return obj


class CreatorRequiredMixin(AccessMixin):
    """
    Mixin que verifica que el usuario actual es el creador de la tarea.

    Debe usarse en vistas de gestión de autores.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        task = self.get_task()
        if task.created_by_id != request.user.pk:
            raise PermissionDenied("Solo el creador puede gestionar autores.")

        return super().dispatch(request, *args, **kwargs)

    def get_task(self):
        """Obtiene la tarea desde URL kwargs."""
        if not hasattr(self, "_task"):
            pk = self.kwargs.get("pk") or self.kwargs.get("task_pk")
            self._task = get_object_or_404(Task.objects.accessible_by(self.request.user), pk=pk)
        return self._task


class TaskOwnerOrAuthorMixin(TaskAccessMixin):
    """
    Mixin que permite acceso a autores y creador.

    Combina TaskAccessMixin con verificación de autor.
    """

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # TaskAccessMixin ya verifica is_author
        return obj


def task_access_required(view_func):
    """
    Decorador para vistas basadas en función que requiere acceso a la tarea.

    Uso:
        @task_access_required
        def mi_vista(request, pk):
            task = request.task  # Disponible tras decorador
    """
    from functools import wraps

    @wraps(view_func)
    def _wrapped_view(request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        task = get_object_or_404(Task.objects.accessible_by(request.user), pk=pk)
        request.task = task
        return view_func(request, pk, *args, **kwargs)

    return _wrapped_view


def creator_required(view_func):
    """
    Decorador para vistas que requieren ser el creador de la tarea.

    Uso:
        @creator_required
        def gestionar_autores(request, pk):
            task = request.task
    """
    from functools import wraps

    @wraps(view_func)
    def _wrapped_view(request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        task = get_object_or_404(Task.objects.accessible_by(request.user), pk=pk)
        if task.created_by_id != request.user.pk:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Solo el creador puede gestionar autores.")

        request.task = task
        return view_func(request, pk, *args, **kwargs)

    return _wrapped_view