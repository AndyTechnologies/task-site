"""
Capa de servicios para operaciones de negocio de Tasks.

Centraliza la lógica de creación, actualización de autores y gestión de colaboradores
en transacciones atómicas con validaciones de permisos.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Task

User = get_user_model()


class TaskService:
    """Servicios para operaciones de Task."""

    @staticmethod
    @transaction.atomic
    def create_task(user, title, body="", author_ids=None):
        """
        Crea una nueva tarea con el usuario autenticado como creador.

        Args:
            user: Usuario autenticado (creador)
            title: Título de la tarea (obligatorio)
            body: Contenido Markdown (opcional)
            author_ids: Lista de IDs de coautores adicionales (opcional)

        Returns:
            Task: La tarea creada

        Raises:
            ValidationError: Si los datos no son válidos
        """
        if not title or not title.strip():
            raise ValidationError({"title": "El título es obligatorio."})

        title = title.strip()
        if len(title) > 200:
            raise ValidationError({"title": "El título no puede exceder 200 caracteres."})

        # Validar coautores: solo usuarios activos y existentes (ignorar inválidos)
        coauthors = User.objects.none()
        if author_ids:
            coauthors = User.objects.filter(pk__in=author_ids, is_active=True)

        # Crear tarea
        task = Task.objects.create(
            title=title.strip(),
            body=body or "",
            created_by=user,
        )

        # Añadir creador + coautores válidos a authors
        author_pks = {user.pk} | set(coauthors.values_list("pk", flat=True))
        task.authors.add(*User.objects.filter(pk__in=author_pks))

        return task

    @staticmethod
    @transaction.atomic
    def update_task(task, user, title=None, body=None, status=None):
        """
        Actualiza campos editables de una tarea.

        Args:
            task: Tarea a actualizar
            user: Usuario que solicita la actualización
            title: Nuevo título (opcional)
            body: Nuevo body Markdown (opcional)
            status: Nuevo estado (opcional)

        Returns:
            Task: La tarea actualizada

        Raises:
            PermissionDenied: Si el usuario no tiene permiso
        """
        if not task.can_edit(user):
            raise PermissionDenied("No tienes permiso para editar esta tarea.")

        if title is not None:
            if not title.strip():
                raise ValidationError({"title": "El título no puede estar vacío."})
            task.title = title.strip()

        if body is not None:
            task.body = body or ""

        if status is not None:
            valid_statuses = [c[0] for c in Task.Status.choices]
            if status not in valid_statuses:
                raise ValidationError({"status": f"Estado inválido. Opciones: {valid_statuses}"})
            task.status = status

        task.save()
        return task

    @staticmethod
    @transaction.atomic
    def update_authors(task, user, author_ids):
        """
        Actualiza la lista de autores de una tarea.

        Solo el creador puede gestionar autores.
        El creador nunca puede ser removido.

        Args:
            task: Tarea a modificar
            user: Usuario que solicita el cambio (debe ser creador)
            author_ids: Lista de IDs de coautores adicionales (sin el creador)

        Returns:
            Task: La tarea actualizada

        Raises:
            PermissionDenied: Si el usuario no es el creador
            ValidationError: Si hay IDs inválidos
        """
        if not task.can_manage_authors(user):
            raise PermissionDenied("Solo el creador puede gestionar autores.")

        # Validar que todos los IDs correspondan a usuarios activos
        valid_users = User.objects.filter(pk__in=author_ids, is_active=True)
        valid_pks = set(valid_users.values_list("pk", flat=True))
        invalid_ids = set(author_ids) - valid_pks

        if invalid_ids:
            raise ValidationError(
                {"authors": f"Los siguientes usuarios no existen o están inactivos: {invalid_ids}"}
            )

        # El creador SIEMPRE debe estar en authors (se añade automáticamente)
        required_pks = {task.created_by_id} | valid_pks

        with transaction.atomic():
            current_pks = set(task.authors.values_list("pk", flat=True))

            # Añadir nuevos (creador + coautores válidos)
            to_add = required_pks - current_pks
            if to_add:
                task.authors.add(*User.objects.filter(pk__in=to_add))

            # Remover los que ya no están (excepto creador)
            to_remove = current_pks - required_pks
            if to_remove:
                task.authors.remove(*to_remove)

        return task

    @staticmethod
    def get_task_or_404(task_pk, user):
        """
        Obtiene una tarea verificando que el usuario tenga acceso.

        Args:
            task_pk: PK de la tarea
            user: Usuario que solicita acceso

        Returns:
            Task: La tarea si el usuario tiene acceso

        Raises:
            PermissionDenied: Si la tarea no existe o el usuario no tiene acceso
        """
        from django.shortcuts import get_object_or_404
        from django.core.exceptions import PermissionDenied
        from django.http import Http404
        try:
            return get_object_or_404(Task.objects.accessible_by(user), pk=task_pk)
        except Http404:
            raise PermissionDenied("No tienes acceso a esta tarea.")