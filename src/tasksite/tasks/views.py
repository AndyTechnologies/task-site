"""
Vistas para Tasks.

CBVs para listado, creación, detalle, edición, búsqueda y gestión de autores.
"""
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView
from django.utils.decorators import method_decorator

from .forms import TaskForm, TaskEditForm, AuthorManagementForm
from .mixins import TaskAccessMixin, CreatorRequiredMixin
from .models import Task
from .services import TaskService
from .utils import render_markdown_safe


class TaskListView(TaskAccessMixin, ListView):
    """
    Listado de tareas accesibles para el usuario autenticado.

    Soporta búsqueda via query param 'q'.
    """

    model = Task
    template_name = "tasks/list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()

        # Búsqueda
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | Q(body__icontains=query)
            )

        return qs.select_related("created_by").prefetch_related("authors")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["page_title"] = "Mis tareas"
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """
    Creación de nueva tarea.

    Usa TaskForm que valida y sanitiza Markdown.
    """

    form_class = TaskForm
    template_name = "tasks/form.html"
    success_url = reverse_lazy("tasks:detail", kwargs={"pk": "REPLACE"})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Guardar tarea (TaskService.create_task se llama en form.save())
        self.object = form.save()
        return redirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nueva tarea"
        context["form_action"] = "Crear"
        # Sidebar: tareas accesibles para navegación
        context["sidebar_tasks"] = Task.objects.accessible_by(self.request.user).select_related("created_by").order_by("-updated_at")
        return context


class TaskDetailView(TaskAccessMixin, DetailView):
    """
    Vista detallada de una tarea.

    Layout de dos paneles: sidebar + contenido principal.
    Renderiza Markdown sanitizado.
    """

    model = Task
    template_name = "tasks/detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return super().get_queryset().select_related("created_by").prefetch_related("authors")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object

        # Renderizar body Markdown de forma segura
        from .utils import render_markdown_safe
        context["rendered_body"] = render_markdown_safe(task.body)

        # Sidebar: tareas accesibles para navegación
        context["sidebar_tasks"] = Task.objects.accessible_by(self.request.user).select_related("created_by").order_by("-updated_at")

        context["page_title"] = task.title
        return context


class TaskUpdateView(TaskAccessMixin, UpdateView):
    """
    Edición de tarea existente.

    Permite editar título, body y estado. No autores ni creador.
    """

    model = Task
    form_class = TaskEditForm
    template_name = "tasks/form.html"
    context_object_name = "task"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar: {self.object.title}"
        context["form_action"] = "Guardar cambios"
        # Sidebar: tareas accesibles para navegación
        context["sidebar_tasks"] = Task.objects.accessible_by(self.request.user).select_related("created_by").order_by("-updated_at")
        return context


class TaskAuthorManagementView(CreatorRequiredMixin, FormView):
    """
    Gestión de autores de una tarea.

    Solo accesible para el creador. Permite añadir/quitar coautores.
    """

    form_class = AuthorManagementForm
    template_name = "tasks/author_form.html"
    success_url = reverse_lazy("tasks:detail", kwargs={"pk": "REPLACE"})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["task"] = self.get_task()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return redirect(self.get_task().get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_task()
        context["task"] = task
        context["page_title"] = f"Gestionar autores: {task.title}"
        return context


class TaskSearchView(TaskAccessMixin, ListView):
    """
    Vista de búsqueda de tareas.

    Extiende ListView con funcionalidad de búsqueda.
    """

    model = Task
    template_name = "tasks/list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q", "").strip()

        if query:
            qs = qs.filter(
                Q(title__icontains=query) | Q(body__icontains=query)
            )

        return qs.select_related("created_by").prefetch_related("authors")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["page_title"] = f"Resultados para: {context['search_query']}" if context['search_query'] else "Mis tareas"
        context["is_search"] = bool(context['search_query'])
        return context


@method_decorator(csrf_exempt, name='dispatch')
class MarkdownPreviewView(LoginRequiredMixin, View):
    """
    Endpoint para vista previa de Markdown en el editor.
    Recibe JSON con {markdown: string} y retorna {html: string}.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            markdown_text = data.get('markdown', '')
            if not isinstance(markdown_text, str):
                return JsonResponse({'error': 'Markdown debe ser string'}, status=400)
            html = render_markdown_safe(markdown_text)
            return JsonResponse({'html': html})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)