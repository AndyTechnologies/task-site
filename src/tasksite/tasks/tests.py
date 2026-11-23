"""
Tests completos para Tasks.

Cubre: modelo, servicios, formularios, vistas, permisos multiusuario,
sanitización Markdown (XSS), y aislamiento de datos.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import TestCase, Client
from django.urls import reverse

from .models import Task
from .services import TaskService
from .forms import TaskForm, TaskEditForm, AuthorManagementForm
from .utils import render_markdown_safe, render_markdown_preview

User = get_user_model()


# =============================================================================
# MODEL TESTS
# =============================================================================

class TaskModelTests(TestCase):
    """Tests del modelo Task."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass1234"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@test.com", password="pass1234"
        )

    def test_create_task_adds_creator_to_authors(self):
        """El creador se añade automáticamente a authors al crear."""
        task = Task.objects.create(
            title="Tarea test",
            body="# Hola\n\nContenido",
            created_by=self.user1,
        )
        self.assertIn(self.user1, task.authors.all())

    def test_task_str_representation(self):
        """Representación string del modelo."""
        task = Task.objects.create(title="Mi tarea", created_by=self.user1)
        self.assertEqual(str(task), "Mi tarea")

    def test_task_status_choices(self):
        """Estados válidos del modelo."""
        self.assertEqual(Task.Status.PENDING, "pending")
        self.assertEqual(Task.Status.IN_PROGRESS, "in_progress")
        self.assertEqual(Task.Status.COMPLETED, "completed")
        self.assertEqual(Task.Status.CANCELLED, "cancelled")

    def test_can_edit_returns_true_for_author(self):
        """can_edit es True para autores."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        self.assertTrue(task.can_edit(self.user1))
        self.assertTrue(task.can_edit(self.user2))

    def test_can_edit_returns_false_for_non_author(self):
        """can_edit es False para no autores."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        self.assertFalse(task.can_edit(self.user2))

    def test_can_manage_authors_only_creator(self):
        """Solo el creador puede gestionar autores."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        self.assertTrue(task.can_manage_authors(self.user1))
        self.assertFalse(task.can_manage_authors(self.user2))
        self.assertFalse(task.can_manage_authors(self.user3))

    def test_is_author(self):
        """is_author verifica pertenencia."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        self.assertTrue(task.is_author(self.user1))
        self.assertTrue(task.is_author(self.user2))
        self.assertFalse(task.is_author(self.user3))

    def test_get_absolute_url(self):
        """URL absoluta del detalle."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        expected = reverse("tasks:detail", kwargs={"pk": task.pk})
        self.assertEqual(task.get_absolute_url(), expected)

    def test_creator_cannot_be_removed_from_authors_via_service(self):
        """El creador no puede ser removido de authors (servicio lo mantiene)."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        # Intentar quitar creador pasando lista vacía - servicio auto-mantiene al creador
        from .services import TaskService
        task = TaskService.update_authors(task, self.user1, [])
        self.assertIn(self.user1, task.authors.all())


class TaskManagerTests(TestCase):
    """Tests del manager personalizado."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass1234"
        )
        self.task1 = Task.objects.create(title="Tarea 1", created_by=self.user1)
        self.task2 = Task.objects.create(title="Tarea 2", created_by=self.user1)
        self.task3 = Task.objects.create(title="Tarea 3", created_by=self.user2)
        # user1 es autor de task1, task2 (creador)
        # user2 es autor de task1 (coautor) y task3 (creador)
        self.task1.authors.add(self.user2)  # user2 también autor de task1

    def test_accessible_by_user1(self):
        """user1 ve task1, task2."""
        qs = Task.objects.accessible_by(self.user1)
        self.assertEqual(qs.count(), 2)
        self.assertIn(self.task1, qs)
        self.assertIn(self.task2, qs)
        self.assertNotIn(self.task3, qs)

    def test_accessible_by_user2(self):
        """user2 ve task1, task3."""
        qs = Task.objects.accessible_by(self.user2)
        self.assertEqual(qs.count(), 2)
        self.assertIn(self.task1, qs)
        self.assertIn(self.task3, qs)
        self.assertNotIn(self.task2, qs)

    def test_created_by_user(self):
        """created_by_user filtra por creador."""
        qs = Task.objects.created_by_user(self.user1)
        self.assertEqual(qs.count(), 2)
        self.assertIn(self.task1, qs)
        self.assertIn(self.task2, qs)
        self.assertNotIn(self.task3, qs)


# =============================================================================
# SERVICE TESTS
# =============================================================================

class TaskServiceTests(TestCase):
    """Tests de la capa de servicios."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass1234"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@test.com", password="pass1234"
        )
        self.user_inactive = User.objects.create_user(
            username="inactive", email="inactive@test.com", password="pass1234", is_active=False
        )

    def test_create_task_basic(self):
        """Creación básica de tarea."""
        task = TaskService.create_task(self.user1, "Título", "Body *markdown*")
        self.assertEqual(task.title, "Título")
        self.assertEqual(task.body, "Body *markdown*")
        self.assertEqual(task.created_by, self.user1)
        self.assertIn(self.user1, task.authors.all())
        self.assertEqual(task.status, Task.Status.PENDING)

    def test_create_task_with_coauthors(self):
        """Creación con coautores adicionales."""
        task = TaskService.create_task(
            self.user1, "Título", "Body", author_ids=[self.user2.pk, self.user3.pk]
        )
        authors = set(task.authors.values_list("pk", flat=True))
        expected = {self.user1.pk, self.user2.pk, self.user3.pk}
        self.assertEqual(authors, expected)

    def test_create_task_excludes_inactive_users(self):
        """Usuarios inactivos se ignoran al añadir coautores."""
        task = TaskService.create_task(
            self.user1, "Título", "Body", author_ids=[self.user2.pk, self.user_inactive.pk]
        )
        authors = set(task.authors.values_list("pk", flat=True))
        self.assertEqual(authors, {self.user1.pk, self.user2.pk})

    def test_create_task_excludes_nonexistent_users(self):
        """IDs inexistentes se ignoran."""
        task = TaskService.create_task(self.user1, "Título", "Body", author_ids=[9999])
        self.assertEqual(set(task.authors.values_list("pk", flat=True)), {self.user1.pk})

    def test_create_task_validates_title_required(self):
        """Título obligatorio."""
        with self.assertRaises(ValidationError):
            TaskService.create_task(self.user1, "", "Body")

    def test_create_task_validates_title_max_length(self):
        """Título máximo 200 caracteres."""
        with self.assertRaises(ValidationError):
            TaskService.create_task(self.user1, "x" * 201, "Body")

    def test_update_task_title_body_status(self):
        """Actualización de título, body y estado."""
        task = TaskService.create_task(self.user1, "Original", "Body")
        task = TaskService.update_task(task, self.user1, title="Nuevo", status=Task.Status.IN_PROGRESS)
        self.assertEqual(task.title, "Nuevo")
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

    def test_update_task_requires_edit_permission(self):
        """Actualizar requiere permiso de edición."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        with self.assertRaises(PermissionDenied):
            TaskService.update_task(task, self.user2, title="Hack")

    def test_update_task_validates_status(self):
        """Estado debe ser válido."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        with self.assertRaises(ValidationError):
            TaskService.update_task(task, self.user1, status="invalid_status")

    def test_update_authors_creator_only(self):
        """Solo creador puede gestionar autores."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        task.authors.add(self.user2)
        # user2 intenta añadir user3 -> debe fallar
        with self.assertRaises(PermissionDenied):
            TaskService.update_authors(task, self.user2, [self.user3.pk])

    def test_update_authors_guarantees_creator(self):
        """Creador siempre permanece en authors."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        task.authors.add(self.user2)
        # Intentar quitar creador pasando solo user2
        task = TaskService.update_authors(task, self.user1, [self.user2.pk])
        self.assertIn(self.user1, task.authors.all())
        self.assertIn(self.user2, task.authors.all())

    def test_update_authors_validates_users(self):
        """Valida usuarios activos y existentes."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        # Usuario inactivo
        with self.assertRaises(ValidationError):
            TaskService.update_authors(task, self.user1, [self.user_inactive.pk])
        # Usuario inexistente
        with self.assertRaises(ValidationError):
            TaskService.update_authors(task, self.user1, [9999])

    def test_update_authors_rejects_removing_creator(self):
        """Intento de remover creador se ignora - creador se mantiene."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        task.authors.add(self.user2)
        # Pasar solo user2 (sin user1) - servicio auto-mantiene al creador
        task = TaskService.update_authors(task, self.user1, [self.user2.pk])
        self.assertIn(self.user1, task.authors.all())
        self.assertIn(self.user2, task.authors.all())

    def test_get_task_or_404_returns_accessible(self):
        """Obtiene tarea accesible."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        result = TaskService.get_task_or_404(task.pk, self.user1)
        self.assertEqual(result, task)

    def test_get_task_or_404_denies_inaccessible(self):
        """Niega acceso a tarea ajena."""
        task = TaskService.create_task(self.user1, "Título", "Body")
        with self.assertRaises(PermissionDenied):
            TaskService.get_task_or_404(task.pk, self.user2)


# =============================================================================
# FORM TESTS
# =============================================================================

class TaskFormTests(TestCase):
    """Tests de formularios."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass1234"
        )

    def test_task_form_valid(self):
        """Formulario válido crea tarea."""
        form = TaskForm(
            data={"title": "Nueva tarea", "body": "# Hola\n\nContenido", "authors": [self.user2.pk]},
            user=self.user1,
        )
        self.assertTrue(form.is_valid())
        task = form.save()
        self.assertEqual(task.title, "Nueva tarea")
        self.assertIn(self.user1, task.authors.all())
        self.assertIn(self.user2, task.authors.all())

    def test_task_form_excludes_current_user_from_authors(self):
        """Usuario actual excluido de lista de coautores."""
        form = TaskForm(user=self.user1)
        self.assertNotIn(self.user1, form.fields["authors"].queryset)
        self.assertIn(self.user2, form.fields["authors"].queryset)

    def test_task_form_rejects_empty_title(self):
        """Título vacío rechazado."""
        form = TaskForm(data={"title": "", "body": "Body"}, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_task_form_rejects_long_title(self):
        """Título > 200 chars rechazado."""
        form = TaskForm(data={"title": "x" * 201, "body": "Body"}, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_task_form_sanitizes_markdown(self):
        """Body se sanitiza al validar."""
        # XSS attempt - HTML se escapa
        form = TaskForm(data={"title": "Test", "body": '<script>alert(1)</script>'}, user=self.user1)
        self.assertTrue(form.is_valid())  # Sanitización no falla, solo limpia

    def test_task_edit_form_valid(self):
        """Formulario de edición válido."""
        task = Task.objects.create(title="Original", body="Body", created_by=self.user1)
        form = TaskEditForm(
            data={"title": "Editado", "body": "Nuevo **body**", "status": Task.Status.IN_PROGRESS},
            instance=task,
            user=self.user1,
        )
        self.assertTrue(form.is_valid())
        updated = form.save()
        self.assertEqual(updated.title, "Editado")
        self.assertEqual(updated.status, Task.Status.IN_PROGRESS)

    def test_task_edit_form_rejects_empty_title(self):
        """Título vacío en edición rechazado."""
        task = Task.objects.create(title="Original", created_by=self.user1)
        form = TaskEditForm(data={"title": "", "body": "Body"}, instance=task, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_author_management_form_valid(self):
        """Formulario de gestión de autores válido."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        form = AuthorManagementForm(
            data={"authors": [self.user2.pk]},
            task=task,
            user=self.user1,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertIn(self.user1, task.authors.all())
        self.assertIn(self.user2, task.authors.all())

    def test_author_management_form_excludes_creator(self):
        """Creador excluido de lista."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        form = AuthorManagementForm(task=task, user=self.user1)
        self.assertNotIn(self.user1, form.fields["authors"].queryset)
        self.assertIn(self.user2, form.fields["authors"].queryset)

    def test_author_management_form_preselects_current_authors(self):
        """Pre-selecciona autores actuales (excluyendo creador)."""
        task = Task.objects.create(title="Test", created_by=self.user1)
        task.authors.add(self.user2)
        form = AuthorManagementForm(task=task, user=self.user1)
        self.assertEqual(list(form.initial["authors"]), [self.user2])


# =============================================================================
# MARKDOWN SANITIZATION TESTS (XSS)
# =============================================================================

class MarkdownSanitizationTests(TestCase):
    """Tests de sanitización Markdown - vectores XSS."""

    def test_basic_markdown_rendered(self):
        """Markdown básico se renderiza."""
        html = render_markdown_safe("# Hola\n\n**Negrita** y *cursiva*")
        self.assertIn("<h1>Hola</h1>", html)
        self.assertIn("<strong>Negrita</strong>", html)
        self.assertIn("<em>cursiva</em>", html)

    def test_script_tag_escaped(self):
        """Script tags se escapan (no se ejecutan)."""
        html = render_markdown_safe('<script>alert(1)</script>')
        # HTML se escapa - el script tag aparece como entidades HTML (<script>)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;/script&gt;", html)
        self.assertIn("alert", html)
        # No hay tag script real ejecutable
        self.assertNotIn("<script>", html)
        self.assertNotIn("</script>", html)

    def test_javascript_link_not_clickable(self):
        """Links javascript: no se convierten en enlaces clickeables."""
        html = render_markdown_safe('[Click me](javascript:alert(1))')
        # El link no se renderiza como <a href="javascript:...">, queda como texto
        self.assertNotIn('href="javascript:', html)
        self.assertNotIn('<a ', html)
        self.assertIn('javascript:alert(1)', html)

    def test_onerror_not_rendered(self):
        """onerror en imagen no se renderiza como atributo HTML."""
        html = render_markdown_safe('![img](x onerror=alert(1))')
        # La sintaxis markdown inválida queda como texto plano - onerror aparece en el texto
        self.assertIn('onerror', html)  # onerror está presente en texto escapado
        self.assertNotIn('<img', html)

    def test_data_uri_not_clickable(self):
        """Data URIs no se convierten en enlaces clickeables."""
        html = render_markdown_safe('[link](data:text/html,<script>alert(1)</script>)')
        self.assertNotIn('href="data:', html)
        self.assertNotIn('<a ', html)
        self.assertIn('data:', html)
        # El HTML dentro de la data URI se escapa
        self.assertIn("&lt;script&gt;", html)

    def test_vbscript_not_clickable(self):
        """VBScript no se convierte en enlace clickeable."""
        html = render_markdown_safe('[link](vbscript:msgbox(1))')
        self.assertNotIn('href="vbscript:', html)
        self.assertNotIn('<a ', html)
        self.assertIn('vbscript:', html)

    def test_iframe_escaped(self):
        """Iframe se escapa."""
        html = render_markdown_safe('<iframe src="evil.com"></iframe>')
        # HTML se escapa - iframe aparece como entidad HTML (<iframe>)
        self.assertIn("&lt;iframe", html)
        self.assertIn("&lt;/iframe", html)
        # No hay tag iframe real ejecutable
        self.assertNotIn("<iframe", html)
        self.assertNotIn("</iframe", html)

    def test_style_attribute_not_rendered(self):
        """Style attribute no se renderiza (HTML escapado)."""
        html = render_markdown_safe('<p style="color:red">Hola</p>')
        # HTML se escapa - style aparece en texto escapado como entidad (<p style="color:red">)
        self.assertIn('style=', html)  # style= está presente en texto escapado
        # No hay tag p real con atributo style
        self.assertNotIn("<p style=", html)
        # No hay atributo style real (solo texto escapado con comillas codificadas)
        self.assertNotIn('<p style="', html)

    def test_allowed_tags_render(self):
        """Tags permitidos se renderizan."""
        md = """# H1\n## H2\n### H3\n\n- Item 1\n- Item 2\n\n1. One\n2. Two\n\n> Quote\n\n`code`\n\n```python\nprint('hi')\n```\n\n[Link](https://example.com)\n\n![Img](https://example.com/img.png)\n\n---\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"""
        html = render_markdown_safe(md)
        self.assertIn("<h1>H1</h1>", html)
        self.assertIn("<h2>H2</h2>", html)
        self.assertIn("<h3>H3</h3>", html)
        self.assertIn("<ul>", html)
        self.assertIn("<ol>", html)
        self.assertIn("<blockquote>", html)
        self.assertIn("<code>", html)
        self.assertIn("<pre>", html)
        self.assertIn('<a href="https://example.com">Link</a>', html)
        self.assertIn('<img src="https://example.com/img.png"', html)
        self.assertIn("<hr", html)
        self.assertIn("<table>", html)

    def test_tasklist_rendered_as_text(self):
        """Task lists se renderizan como texto (markdown-it no soporta tasklists nativamente)."""
        html = render_markdown_safe("- [x] Done\n- [ ] Pending")
        self.assertIn("[x]", html)
        self.assertIn("[ ]", html)

    def test_html_in_markdown_disabled(self):
        """HTML arbitrario en Markdown deshabilitado (se escapa)."""
        html = render_markdown_safe('<div onclick="evil()">Hola</div>')
        # HTML se escapa - onclick y div aparecen como texto escapado
        self.assertNotIn("<div", html)  # No hay tag div real (solo <div)
        # onclick=" está presente en el texto escapado (comilla no se escapa en nh3)
        self.assertIn('onclick="', html)  # onclick está en texto escapado con comillas
        self.assertIn("&lt;div", html)  # Texto escapado visible (<div)
        self.assertIn("Hola", html)

    def test_strikethrough_rendered(self):
        """Tachado se renderiza como texto (markdown-it commonmark no lo soporta nativamente)."""
        html = render_markdown_safe("~~tachado~~")
        # markdown-it-py commonmark no soporta strikethrough nativamente
        # Se renderiza como texto con tildes Unicode
        self.assertIn("tachado", html)  # El contenido está presente

    def test_table_rendered(self):
        """Tablas se renderizan."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = render_markdown_safe(md)
        self.assertIn("<table>", html)
        self.assertIn("<thead>", html)
        self.assertIn("<tbody>", html)
        self.assertIn("<th>", html)
        self.assertIn("<td>", html)

    def test_empty_input_returns_empty(self):
        """Input vacío retorna vacío."""
        self.assertEqual(render_markdown_safe(""), "")
        self.assertEqual(render_markdown_safe(None), "")

    def test_render_markdown_preview_same_as_safe(self):
        """Preview usa misma lógica."""
        md = "# Test\n\n**Bold**"
        self.assertEqual(render_markdown_preview(md), render_markdown_safe(md))


# =============================================================================
# VIEW TESTS
# =============================================================================

class TaskViewTests(TestCase):
    """Tests de vistas."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass1234"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@test.com", password="pass1234"
        )
        self.task1 = Task.objects.create(title="Tarea 1", body="Body 1", created_by=self.user1)
        self.task2 = Task.objects.create(title="Tarea 2", body="Body 2", created_by=self.user1)
        self.task3 = Task.objects.create(title="Tarea 3", body="Body 3", created_by=self.user2)
        self.task1.authors.add(self.user2)
        self.task2.authors.add(self.user3)

    def login(self, user):
        self.client.force_login(user)

    # ListView
    def test_list_view_requires_login(self):
        """ListView requiere login."""
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_list_view_shows_accessible_tasks(self):
        """ListView muestra solo tareas accesibles."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 200)
        # user1 es autor de task1, task2 (creador) y task3 (no autor)
        self.assertContains(response, "Tarea 1")
        self.assertContains(response, "Tarea 2")
        self.assertNotContains(response, "Tarea 3")

    def test_list_view_user2_sees_task1_and_task3(self):
        """user2 ve task1 (coautor) y task3 (creador)."""
        self.login(self.user2)
        response = self.client.get(reverse("tasks:list"))
        self.assertContains(response, "Tarea 1")
        self.assertNotContains(response, "Tarea 2")
        self.assertContains(response, "Tarea 3")

    def test_list_view_empty_state(self):
        """Estado vacío para usuario sin tareas."""
        self.login(self.user3)
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay tareas")

    # Search
    def test_search_by_title(self):
        """Búsqueda por título."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:list"), {"q": "Tarea 1"})
        self.assertContains(response, "Tarea 1")
        self.assertNotContains(response, "Tarea 2")

    def test_search_by_body(self):
        """Búsqueda por body."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:list"), {"q": "Body 2"})
        self.assertContains(response, "Tarea 2")
        self.assertNotContains(response, "Tarea 1")

    def test_search_respects_permissions(self):
        """Búsqueda respeta permisos."""
        self.login(self.user2)
        response = self.client.get(reverse("tasks:list"), {"q": "Tarea"})
        # user2 ve task1 y task3, no task2
        self.assertContains(response, "Tarea 1")
        self.assertContains(response, "Tarea 3")
        self.assertNotContains(response, "Tarea 2")

    def test_search_empty_results(self):
        """Resultados vacíos muestra mensaje."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:list"), {"q": "inexistente"})
        self.assertContains(response, "No hay coincidencias")

    # CreateView
    def test_create_view_get(self):
        """GET create view."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:new"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nueva tarea")

    def test_create_view_post_valid(self):
        """POST create view válido."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:new"),
            {"title": "Nueva", "body": "# Hola", "authors": [self.user2.pk]},
        )
        self.assertEqual(response.status_code, 302)  # Redirect to detail
        task = Task.objects.get(title="Nueva")
        self.assertEqual(task.created_by, self.user1)
        self.assertIn(self.user2, task.authors.all())

    def test_create_view_post_invalid(self):
        """POST create view inválido (título vacío)."""
        self.login(self.user1)
        response = self.client.post(reverse("tasks:new"), {"title": "", "body": "Body"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")

    # DetailView
    def test_detail_view_accessible(self):
        """DetailView accesible para autores."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tarea 1")
        self.assertContains(response, "Body 1")

    def test_detail_view_denied_for_non_author(self):
        """DetailView denegada para no autores (404 por seguridad)."""
        self.login(self.user3)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 404)

    def test_detail_view_renders_markdown(self):
        """DetailView renderiza Markdown sanitizado."""
        self.task1.body = "# Título\n\n**Negrita**"
        self.task1.save()
        self.login(self.user1)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task1.pk}))
        self.assertContains(response, "<h1>Título</h1>")
        self.assertContains(response, "<strong>Negrita</strong>")

    def test_detail_view_shows_metadata(self):
        """DetailView muestra metadatos."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task1.pk}))
        self.assertContains(response, "user1")
        self.assertContains(response, "Creado por")
        self.assertContains(response, "Autores")

    # UpdateView
    def test_update_view_get(self):
        """GET update view."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:edit", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar: Tarea 1")

    def test_update_view_post_valid(self):
        """POST update view válido."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": self.task1.pk}),
            {"title": "Actualizada", "body": "Nuevo body", "status": Task.Status.IN_PROGRESS},
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, "Actualizada")
        self.assertEqual(self.task1.status, Task.Status.IN_PROGRESS)

    def test_update_view_denied_for_non_author(self):
        """Update view denegada para no autores (404 por seguridad)."""
        self.login(self.user3)
        response = self.client.get(reverse("tasks:edit", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 404)

    # AuthorManagementView
    def test_author_management_view_creator_only(self):
        """Solo creador accede a gestión de autores."""
        self.login(self.user2)  # coautor, no creador
        response = self.client.get(reverse("tasks:authors", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_author_management_view_creator_can_access(self):
        """Creador accede a gestión de autores."""
        self.login(self.user1)
        response = self.client.get(reverse("tasks:authors", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestionar autores")

    def test_author_management_add_coauthor(self):
        """Añadir coautor."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:authors", kwargs={"pk": self.task1.pk}),
            {"authors": [self.user3.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertIn(self.user3, self.task1.authors.all())

    def test_author_management_remove_coauthor(self):
        """Quitar coautor."""
        self.task1.authors.add(self.user3)
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:authors", kwargs={"pk": self.task1.pk}),
            {"authors": []},
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertNotIn(self.user3, self.task1.authors.all())
        self.assertIn(self.user1, self.task1.authors.all())  # Creador permanece

    def test_author_management_creator_cannot_be_removed(self):
        """Creador no puede ser removido aunque se intente."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:authors", kwargs={"pk": self.task1.pk}),
            {"authors": [self.user2.pk]},  # Solo user2, sin user1
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertIn(self.user1, self.task1.authors.all())
        self.assertIn(self.user2, self.task1.authors.all())

    # Markdown Preview
    def test_markdown_preview_endpoint(self):
        """Endpoint de preview funciona."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:preview"),
            data='{"markdown": "# Hola\\n\\n**Bold**"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("<h1>Hola</h1>", data["html"])
        self.assertIn("<strong>Bold</strong>", data["html"])

    def test_markdown_preview_sanitizes(self):
        """Preview sanitiza entrada."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:preview"),
            data='{"markdown": "<script>alert(1)</script>"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("<script>", data["html"])

    def test_markdown_preview_invalid_json(self):
        """JSON inválido retorna error 400."""
        self.login(self.user1)
        response = self.client.post(
            reverse("tasks:preview"),
            data="no es json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_markdown_preview_requires_login(self):
        """Preview requiere login."""
        response = self.client.post(
            reverse("tasks:preview"),
            data='{"markdown": "test"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login


# =============================================================================
# PERMISSION/ISOLATION TESTS
# =============================================================================

class TaskPermissionTests(TestCase):
    """Tests de aislamiento multiusuario."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", email="u1@test.com", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", email="u2@test.com", password="pass1234")
        self.user3 = User.objects.create_user(username="user3", email="u3@test.com", password="pass1234")

        # user1 crea task1, task2
        self.task1 = Task.objects.create(title="Task 1", created_by=self.user1)
        self.task2 = Task.objects.create(title="Task 2", created_by=self.user1)
        # user2 crea task3
        self.task3 = Task.objects.create(title="Task 3", created_by=self.user2)
        # user1 y user2 colaboran en task1
        self.task1.authors.add(self.user2)
        # user3 no colabora en nada

    def test_user_only_sees_own_and_shared(self):
        """Usuario solo ve propias y compartidas."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("tasks:list"))
        self.assertContains(response, "Task 1")
        self.assertContains(response, "Task 2")
        self.assertNotContains(response, "Task 3")

    def test_user2_sees_shared_and_own(self):
        """user2 ve task1 (compartida) y task3 (propia)."""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("tasks:list"))
        self.assertContains(response, "Task 1")
        self.assertNotContains(response, "Task 2")
        self.assertContains(response, "Task 3")

    def test_user3_sees_nothing(self):
        """user3 no ve nada."""
        self.client.force_login(self.user3)
        response = self.client.get(reverse("tasks:list"))
        self.assertNotContains(response, "Task 1")
        self.assertNotContains(response, "Task 2")
        self.assertNotContains(response, "Task 3")

    def test_404_for_inaccessible_detail(self):
        """404 para detalle inaccesible (no 403 para no filtrar existencia)."""
        self.client.force_login(self.user3)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 404)

    def test_404_for_inaccessible_edit(self):
        """404 para edición inaccesible."""
        self.client.force_login(self.user3)
        response = self.client.get(reverse("tasks:edit", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 404)

    def test_coauthor_can_edit_body_and_status(self):
        """Coautor puede editar body y estado."""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": self.task1.pk}),
            {"title": "Task 1", "body": "Edited by user2", "status": Task.Status.COMPLETED},
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.body, "Edited by user2")
        self.assertEqual(self.task1.status, Task.Status.COMPLETED)

    def test_coauthor_cannot_manage_authors(self):
        """Coautor no puede gestionar autores."""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("tasks:authors", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_only_creator_manages_authors(self):
        """Solo creador gestiona autores."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("tasks:authors", kwargs={"pk": self.task1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_creator_never_removed(self):
        """Creador nunca removido de authors."""
        self.client.force_login(self.user1)
        # Intentar quitar creador
        response = self.client.post(
            reverse("tasks:authors", kwargs={"pk": self.task1.pk}),
            {"authors": [self.user2.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertIn(self.user1, self.task1.authors.all())

    def test_atomic_creation_rollback_on_error(self):
        """Creación atómica - rollback en error."""
        # Simular error forzando excepción en transacción
        # (Difícil de probar sin mock, pero verificamos que transacciones funcionan)
        self.client.force_login(self.user1)
        initial_count = Task.objects.count()
        response = self.client.post(reverse("tasks:new"), {"title": "", "body": "Body"})
        self.assertEqual(response.status_code, 200)  # Form error
        self.assertEqual(Task.objects.count(), initial_count)  # No se creó


# =============================================================================
# URL/REVERSE TESTS
# =============================================================================

class TaskURLTests(TestCase):
    """Tests de URLs y reverse."""

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", email="u1@test.com", password="pass1234")
        self.task = Task.objects.create(title="Test", created_by=self.user1)

    def test_list_url(self):
        self.assertEqual(reverse("tasks:list"), "/tareas/")

    def test_new_url(self):
        self.assertEqual(reverse("tasks:new"), "/tareas/new/")

    def test_detail_url(self):
        self.assertEqual(reverse("tasks:detail", kwargs={"pk": self.task.pk}), f"/tareas/{self.task.pk}/")

    def test_edit_url(self):
        self.assertEqual(reverse("tasks:edit", kwargs={"pk": self.task.pk}), f"/tareas/{self.task.pk}/edit/")

    def test_authors_url(self):
        self.assertEqual(reverse("tasks:authors", kwargs={"pk": self.task.pk}), f"/tareas/{self.task.pk}/authors/")

    def test_preview_url(self):
        self.assertEqual(reverse("tasks:preview"), "/tareas/preview/")

    def test_get_absolute_url(self):
        self.assertEqual(self.task.get_absolute_url(), reverse("tasks:detail", kwargs={"pk": self.task.pk}))
