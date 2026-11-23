"""
E2E Tests for Search (S5).

Tests the search dialog, search by title/content, results display,
empty results, and dialog interactions (Escape, focus restoration).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_list,
    search_tasks,
    open_search_dialog,
    close_search_dialog,
)

pytestmark = pytest.mark.e2e


class TestSearchDialog:
    """Tests for the search dialog."""

    def test_opens_search_dialog(self, page: Page, live_server_url: str, authenticated_page):
        """Search button opens dialog."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)

        # Dialog should be open
        expect(authenticated_page.locator("#search-dialog[open]")).to_be_visible()
        expect(authenticated_page.get_by_role("heading", name="Buscar tareas")).to_be_visible()

    def test_focus_on_search_input(self, page: Page, live_server_url: str, authenticated_page):
        """Search input receives focus when dialog opens."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)

        # Input should be focused
        search_input = authenticated_page.get_by_label("Término de búsqueda")
        expect(search_input).to_be_focused()

    def test_close_dialog_with_cancel(self, page: Page, live_server_url: str, authenticated_page):
        """Cancel button closes dialog."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)
        close_search_dialog(authenticated_page)

        expect(authenticated_page.locator("#search-dialog[open]")).not_to_be_visible()

    def test_close_dialog_with_escape(self, page: Page, live_server_url: str, authenticated_page):
        """Escape key closes dialog."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)
        authenticated_page.keyboard.press("Escape")

        expect(authenticated_page.locator("#search-dialog[open]")).not_to_be_visible()

    def test_focus_restored_after_close(self, page: Page, live_server_url: str, authenticated_page):
        """Focus returns to search trigger after closing."""
        go_to_task_list(authenticated_page, live_server_url)

        # Get the search trigger button
        search_trigger = authenticated_page.get_by_role("button", name="Buscar tareas")

        open_search_dialog(authenticated_page)
        close_search_dialog(authenticated_page)

        # Focus should return to trigger
        expect(search_trigger).to_be_focused()


class TestSearchFunctionality:
    """Tests for search functionality."""

    def test_search_by_title(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Search finds tasks by title."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "Task 1")

        # Should show only matching task
        expect(authenticated_page.get_by_text("Task 1")).to_be_visible()
        expect(authenticated_page.get_by_text("Task 2")).not_to_be_visible()

    def test_search_by_body_content(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Search finds tasks by body content."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "test")

        expect(authenticated_page.get_by_text("Test Task")).to_be_visible()

    def test_search_case_insensitive(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Search is case insensitive."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "TEST")

        expect(authenticated_page.get_by_text("Test Task")).to_be_visible()

    def test_search_partial_match(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Search matches partial terms."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "Task")

        # Should show all 5 tasks
        task_articles = authenticated_page.locator(".task-item").all()
        assert len(task_articles) == 5

    def test_no_results_message(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Shows message when no results found."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "nonexistent")

        expect(authenticated_page.get_by_text('No hay coincidencias para "nonexistent"')).to_be_visible()
        expect(authenticated_page.get_by_text("Intenta con otros términos o limpia la búsqueda.")).to_be_visible()

    def test_clear_search(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Clear search restores full list."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "Task 1")

        # Click clear search link
        authenticated_page.get_by_role("link", name="Limpiar búsqueda").click()
        authenticated_page.wait_for_load_state("networkidle")

        # Should show all tasks again
        task_articles = authenticated_page.locator(".task-item").all()
        assert len(task_articles) == 5


class TestSearchURLPersistence:
    """Tests for search query persistence in URL."""

    def test_search_query_in_url(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Search query appears in URL."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "Test Task")

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/?q=Test+Task")

    def test_search_preserved_on_reload(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Search preserved after page reload."""
        go_to_task_list(authenticated_page, live_server_url)

        search_tasks(authenticated_page, live_server_url, "Test Task")

        # Reload
        authenticated_page.reload()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/?q=Test+Task")
        expect(authenticated_page.get_by_text("Test Task")).to_be_visible()


class TestSearchAccessibility:
    """Tests for search accessibility."""

    def test_search_dialog_has_aria_labels(self, page: Page, live_server_url: str, authenticated_page):
        """Search dialog has proper ARIA attributes."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)

        dialog = authenticated_page.locator("#search-dialog[open]")
        expect(dialog).to_have_attribute("role", "dialog")
        expect(dialog).to_have_attribute("aria-modal", "true")
        expect(dialog).to_have_attribute("aria-labelledby", "search-dialog-title")

    def test_search_input_has_label(self, page: Page, live_server_url: str, authenticated_page):
        """Search input has accessible label."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)

        expect(authenticated_page.get_by_label("Término de búsqueda")).to_be_visible()

    def test_search_help_text(self, page: Page, live_server_url: str, authenticated_page):
        """Search has help text describing scope."""
        go_to_task_list(authenticated_page, live_server_url)

        open_search_dialog(authenticated_page)

        expect(authenticated_page.get_by_text("Busca en títulos y contenido Markdown de tus tareas accesibles")).to_be_visible()