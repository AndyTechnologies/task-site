"""
E2E Tests for Task Detail (S6).

Tests the task detail view including title, status, creator,
dates, authors, sidebar navigation, and selection highlighting.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_list,
    go_to_task_detail,
    click_task_in_sidebar,
    click_edit_task_button,
    click_manage_authors_button,
    click_back_to_list,
)

pytestmark = pytest.mark.e2e


class TestTaskDetailDisplay:
    """Tests for task detail view display."""

    def test_shows_task_title(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view shows task title."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_role("heading", name=task_basic.title)).to_be_visible()

    def test_shows_task_status(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view shows task status badge."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_text("Pendiente")).to_be_visible()

    def test_shows_creator(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view shows creator."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_text(f"Creado por: {task_basic.created_by.username}")).to_be_visible()

    def test_shows_created_date(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view shows creation date."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_text("Creado:")).to_be_visible()

    def test_shows_updated_date(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view shows last updated date."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_text("Actualizado:")).to_be_visible()

    def test_shows_authors_list(self, page: Page, live_server_url: str, authenticated_page, task_with_coauthor):
        """Detail view shows all authors with creator marked."""
        go_to_task_detail(authenticated_page, live_server_url, task_with_coauthor.pk)

        # Creator marked
        expect(authenticated_page.get_by_text("creator (creador)")).to_be_visible()
        # Coauthor listed
        expect(authenticated_page.get_by_text("coauthor")).to_be_visible()

    def test_shows_rendered_markdown(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Detail view renders Markdown body."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        # Check rendered markdown elements
        expect(authenticated_page.locator(".markdown-preview h1")).to_contain_text("Hello")
        expect(authenticated_page.locator(".markdown-preview strong")).to_contain_text("test")


class TestTaskDetailNavigation:
    """Tests for navigation from task detail."""

    def test_edit_button_navigates_to_edit(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Edit button goes to edit page."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        click_edit_task_button(authenticated_page)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/edit/")

    def test_authors_button_for_creator(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Creator sees authors management button."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        click_manage_authors_button(authenticated_page)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/authors/")

    def test_no_authors_button_for_coauthor(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor does not see authors button."""
        go_to_task_detail(coauthor_page, live_server_url, task_with_coauthor.pk)

        expect(coauthor_page.get_by_role("link", name="Autores")).not_to_be_visible()

    def test_back_to_list(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Back link returns to task list."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        click_back_to_list(authenticated_page)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/")


class TestSidebarNavigation:
    """Tests for sidebar navigation."""

    def test_sidebar_shows_accessible_tasks(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Sidebar lists all accessible tasks."""
        go_to_task_list(authenticated_page, live_server_url)

        # Check sidebar items
        sidebar_items = authenticated_page.locator(".sidebar-item").all()
        assert len(sidebar_items) >= 5

    def test_sidebar_highlights_current_task(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Current task is highlighted in sidebar."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        # Current task should have active class
        active_item = authenticated_page.locator(".sidebar-item.active")
        expect(active_item).to_contain_text(task_basic.title)

    def test_click_sidebar_task_navigates(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Clicking sidebar task navigates to detail."""
        go_to_task_list(authenticated_page, live_server_url)

        click_task_in_sidebar(authenticated_page, task_multiple[0].title)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/{task_multiple[0].pk}/")

    def test_sidebar_updates_on_navigation(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Sidebar highlight updates when navigating."""
        go_to_task_detail(authenticated_page, live_server_url, task_multiple[0].pk)

        expect(authenticated_page.locator(".sidebar-item.active")).to_contain_text(task_multiple[0].title)

        # Navigate to another task
        click_task_in_sidebar(authenticated_page, task_multiple[1].title)

        expect(authenticated_page.locator(".sidebar-item.active")).to_contain_text(task_multiple[1].title)


class TestTaskDetailAccessibility:
    """Tests for task detail accessibility."""

    def test_headings_structure(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Proper heading hierarchy."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        # Main title is h1
        expect(authenticated_page.get_by_role("heading", level=1, name=task_basic.title)).to_be_visible()

        # Meta sections have proper structure
        expect(authenticated_page.get_by_text("Creado por:")).to_be_visible()
        expect(authenticated_page.get_by_text("Autores:")).to_be_visible()

    def test_article_role(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Task detail has article role."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.locator("article[role='article']")).to_be_visible()


class TestStatusChangeReflection:
    """Tests that status changes are reflected in detail view."""

    def test_status_update_shows_in_detail(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Status change appears in detail view after edit."""
        from tests.e2e.helpers.navigation import go_to_task_edit, click_save_changes

        # Edit task and change status
        go_to_task_edit(authenticated_page, live_server_url, task_basic.pk)
        authenticated_page.get_by_label("Estado").select_option("in_progress")
        click_save_changes(authenticated_page)

        # Back in detail view
        expect(authenticated_page.get_by_text("En proceso")).to_be_visible()