from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskManager(models.Manager):
    """Manager personalizado para consultas comunes de tareas."""

    def accessible_by(self, user):
        """Retorna tareas accesibles para un usuario (donde está en authors)."""
        return self.filter(authors=user)

    def created_by_user(self, user):
        """Retorna tareas creadas por un usuario."""
        return self.filter(created_by=user)


class Task(models.Model):
    """Modelo de tarea colaborativa con soporte Markdown."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendiente")
        IN_PROGRESS = "in_progress", _("En proceso")
        COMPLETED = "completed", _("Realizada")
        CANCELLED = "cancelled", _("Cancelada")

    title = models.CharField(
        _("título"),
        max_length=200,
        help_text=_("Título descriptivo de la tarea"),
    )
    body = models.TextField(
        _("cuerpo"),
        blank=True,
        help_text=_("Contenido en Markdown. Soporta encabezados, listas, código, enlaces, etc."),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
        verbose_name=_("creado por"),
        help_text=_("Usuario que creó la tarea. No modificable."),
    )
    authors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="tasks",
        verbose_name=_("autores"),
        help_text=_("Usuarios que pueden ver y editar esta tarea. El creador se incluye automáticamente."),
    )
    created_at = models.DateTimeField(_("creado en"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado en"), auto_now=True)

    objects = TaskManager()

    class Meta:
        verbose_name = _("tarea")
        verbose_name_plural = _("tareas")
        ordering = ["-updated_at"]
        db_table = "tasks_task"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Asegurar que el creador esté en authors
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            self.authors.add(self.created_by)

    def can_edit(self, user):
        """Verifica si un usuario puede editar la tarea (body y estado)."""
        return self.authors.filter(pk=user.pk).exists()

    def can_manage_authors(self, user):
        """Verifica si un usuario puede gestionar autores (solo creador)."""
        return self.created_by_id == user.pk

    def is_author(self, user):
        """Verifica si un usuario es autor de la tarea."""
        return self.authors.filter(pk=user.pk).exists()

    def get_absolute_url(self):
        """URL absoluta para el detalle de la tarea."""
        from django.urls import reverse
        return reverse("tasks:detail", kwargs={"pk": self.pk})