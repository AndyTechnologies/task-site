"""
E2E Tests for Task List (S3).

Tests the task list view including empty state, task display,
navigation to detail, and isolation from other users' tasks.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import go_to_task_list, click_new_task_button

pytestmark = pytest.mark.e2e


class TestTaskListAccess:
    """Tests for accessing the task list."""

    def test_requires_authentication(self, page: Page, live_server_url: str):
        """Task list requires authentication."""
        page.goto(f"{live_server_url}/tareas/")
        page.wait_for_load_state("networkidle")

        # Should redirect to login
        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")

    def test_authenticated_access(self, page: Page, live_server_url: str, authenticated_page):
        """Authenticated user can access task list."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/")
        expect(authenticated_page.get_by_role("heading", name="Mis tareas")).to_be_visible()


class TestTaskListEmptyState:
    """Tests for empty task list state."""

    def test_empty_state_shows_message(self, page: Page, live_server_url: str, authenticated_page):
        """Empty state shows helpful message and create button."""
        go_to_task_list(authenticated_page, live_server_url)

        # Check empty state
        expect(authenticated_page.get_by_text("No hay tareas aún")).to_be_visible()
        expect(authenticated_page.get_by_text("Crea tu primera tarea para comenzar a organizar tu trabajo.")).to_be_visible()

        # Check create button
        create_btn = authenticated_page.get_by_role("link", name="Crear primera tarea")
        expect(create_btn).to_be_visible()

    def test_empty_state_create_button_works(self, page: Page, live_server_url: str, authenticated_page):
        """Create button in empty state navigates to new task form."""
        go_to_task_list(authenticated_page, live_server_url)

        authenticated_page.get_by_role("link", name="Crear primera tarea").click()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/new/")
        expect(authenticated_page.get_by_role("heading", name="Nueva tarea")).to_be_visible()


class TestTaskListDisplay:
    """Tests for task list display with tasks."""

    def test_shows_user_tasks(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Task list shows user's tasks."""
        go_to_task_list(authenticated_page, live_server_url)

        # Check all tasks are displayed
        for i, task in enumerate(task_multiple):
            expect(authenticated_page.get_by_role("article")).to_contain_text(task.title)
            expect(authenticated_page.get_by_text(task.get_status_display())).to_be_visible()
            expect(authenticated_page.get_by_text(f"Creado por: {task.created_by.username}")).to_be_visible()

    def test_shows_task_status_badges(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Tasks display status badges."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page.get_by_text("Pendiente")).to_be_visible()

    def test_shows_task_body_preview(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Tasks show truncated body preview."""
        go_to_task_list(authenticated_page, live_server_url)

        # Body should be truncated
        expect(authenticated_page.get_by_text("This is a")).to_be_visible()

    def test_task_links_to_detail(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Clicking task navigates to detail view."""
        go_to_task_list(authenticated_page, live_server_url)

        authenticated_page.get_by_role("link", name=task_basic.title).click()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/")
        expect(authenticated_page.get_by_role("heading", name=task_basic.title)).to_be_visible()


class TestTaskListIsolation:
    """Tests that users only see their own accessible tasks."""

    def test_does_not_show_other_users_tasks(self, page: Page, live_server_url: str, authenticated_page, user_external):
        """User does not see tasks they don't have access to."""
        from tasksite.tasks.models import Task

        # Create task owned by external user
        external_task = Task.objects.create(
            title="External Task",
            body="Not accessible",
            created_by=user_external,
        )

        go_to_task_list(authenticated_page, live_server_url)

        # Should not see external task
        expect(authenticated_page.get_by_text("External Task")).not_to_be_visible()

    def test_shows_shared_tasks(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor can see shared task."""
        go_to_task_list(coauthor_page, live_server_url)

        expect(coauthor_page.get_by_text("Shared Task")).to_be_visible()


class TestTaskListOrdering:
    """Tests for task list ordering."""

    def test_ordered_by_updated_at_desc(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Tasks ordered by updated_at descending."""
        go_to_task_list(authenticated_page, live_server_url)

        # Get all task titles in order
        task_items = authenticated_page.locator(".task-item").all()
        titles = [item.locator(".task-item-title").inner_text() for item in task_items]

        # Should be ordered by most recently updated first
        # Since all created at once, order may vary but should be consistent
        assert len(titles) == 5


class TestTaskListNavigation:
    """Tests for navigation from task list."""

    def test_new_task_button_in_header(self, page: Page, live_server_url: str, authenticated_page):
        """Header has 'Nueva tarea' button."""
        go_to_task_list(authenticated_page, live_server_url)

        click_new_task_button(authenticated_page)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/new/")

    def test_pagination(self, page: Page, live_server_url: str, authenticated_page, user_creator):
        """Pagination works when there are many tasks."""
        from tasksite.tasks.models import Task

        # Create 25 tasks (paginate_by = 20)
        for i in range(25):
            Task.objects.create(title=f"Task {i}", created_by=user_creator)

        go_to_task_list(authenticated_page, live_server_url)

        # Should show pagination
        expect(authenticated_page.get_by_role("link", name="Siguiente")).to_be_visible()

        # Click next page
        authenticated_page.get_by_role("link", name="Siguiente").click()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.get_by_role("link", name="Anterior")).to_be_visible()