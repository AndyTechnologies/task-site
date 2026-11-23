"""
Formularios para Tasks.

Incluye validación, sanitización Markdown y gestión de coautores.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Task
from .utils import render_markdown_safe

User = get_user_model()


class TaskForm(forms.ModelForm):
    """
    Formulario para crear tareas.

    Incluye título, body Markdown y selección de coautores.
    """

    authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-multiselect',
            'size': '6',
        }),
        label=_("Coautores (opcional)"),
        help_text=_("Mantén Ctrl/Cmd para seleccionar múltiples. Solo usuarios activos. El creador se añade automáticamente."),
    )

    class Meta:
        model = Task
        fields = ["title", "body", "authors"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": _("Título de la tarea"),
                "maxlength": 200,
            }),
            "body": forms.Textarea(attrs={
                "class": "editor-textarea",
                "placeholder": _("# Título principal\n\nTexto en **negrita**, *cursiva*, `código inline`\n\n## Subtítulo\n\n- Lista desordenada\n- Otro item\n\n1. Lista ordenada\n2. Segundo item\n\n```python\ndef hola():\n    print(\"Hola, TaskSite!\")\n```\n\n> Cita importante\n\n[Enlace](https://example.com)\n\n---\n\n- [x] Tarea completada\n- [ ] Tarea pendiente"),
                "spellcheck": "true",
                "rows": 20,
                "readonly": "false",
                "autocomplete": "off",
            }),
        }
        labels = {
            "title": _("Título"),
            "body": _("Body (Markdown)"),
        }
        help_texts = {
            "title": _("Máximo 200 caracteres. Requerido."),
            "body": _("Contenido en Markdown. Soporta encabezados, listas, código, enlaces, etc."),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Excluir al usuario actual de la lista de coautores (se añade automáticamente)
        if self.user:
            self.fields["authors"].queryset = User.objects.filter(is_active=True).exclude(pk=self.user.pk)

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError(_("El título es obligatorio."))
        if len(title) > 200:
            raise ValidationError(_("El título no puede exceder 200 caracteres."))
        return title

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        # Validar que el Markdown se puede sanitizar correctamente
        try:
            render_markdown_safe(body)
        except Exception as e:
            raise ValidationError(_("Error al procesar el Markdown: %(error)s") % {"error": str(e)})
        return body

    def save(self, commit=True):
        from .services import TaskService

        title = self.cleaned_data["title"]
        body = self.cleaned_data["body"]
        author_ids = [u.pk for u in self.cleaned_data.get("authors", [])]

        task = TaskService.create_task(self.user, title, body, author_ids)
        return task


class TaskEditForm(forms.ModelForm):
    """
    Formulario para editar tareas existentes.

    Permite editar título, body y estado. No permite cambiar autores ni creador.
    """

    class Meta:
        model = Task
        fields = ["title", "body", "status"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": _("Título de la tarea"),
                "maxlength": 200,
            }),
            "body": forms.Textarea(attrs={
                "class": "editor-textarea",
                "placeholder": _("Contenido en Markdown..."),
                "spellcheck": "true",
                "rows": 20,
                "readonly": "false",
                "autocomplete": "off",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }
        labels = {
            "title": _("Título"),
            "body": _("Body (Markdown)"),
            "status": _("Estado"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError(_("El título no puede estar vacío."))
        return title

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        try:
            render_markdown_safe(body)
        except Exception as e:
            raise ValidationError(_("Error al procesar el Markdown: %(error)s") % {"error": str(e)})
        return body

    def save(self, commit=True):
        from .services import TaskService

        task = TaskService.update_task(
            self.instance,
            self.user,
            title=self.cleaned_data.get("title"),
            body=self.cleaned_data.get("body"),
            status=self.cleaned_data.get("status"),
        )
        return task


class AuthorManagementForm(forms.Form):
    """
    Formulario para gestionar autores de una tarea.

    Solo accesible para el creador. Permite añadir/quitar coautores.
    """

    authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-multiselect',
            'size': '8',
        }),
        label=_("Autores"),
        help_text=_("Selecciona los usuarios que tendrán acceso a esta tarea. El creador no puede ser removido."),
    )

    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop("task", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Excluir al creador de la lista (no puede ser removido)
        if self.task:
            self.fields["authors"].queryset = User.objects.filter(is_active=True).exclude(pk=self.task.created_by_id)
            # Pre-seleccionar autores actuales (excluyendo creador)
            current_authors = self.task.authors.exclude(pk=self.task.created_by_id)
            self.initial["authors"] = current_authors

    def clean_authors(self):
        authors = self.cleaned_data.get("authors", [])
        # Validar que todos estén activos (el queryset ya lo hace, pero por seguridad)
        for author in authors:
            if not author.is_active:
                raise ValidationError(_("El usuario %(user)s no está activo.") % {"user": author.username})
        return authors

    def save(self):
        from .services import TaskService

        author_ids = [u.pk for u in self.cleaned_data.get("authors", [])]
        return TaskService.update_authors(self.task, self.user, author_ids)