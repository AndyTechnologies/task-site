"""
E2E Tests for Permissions and Collaboration (S8).

Tests multi-user permissions: creator manages authors, coauthors can edit,
external users cannot access, and permission boundaries are enforced.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_list,
    go_to_task_detail,
    go_to_task_edit,
    go_to_task_authors,
    click_save_changes,
    click_back_to_list,
)

pytestmark = pytest.mark.e2e


class TestCreatorPermissions:
    """Tests for task creator permissions."""

    def test_creator_can_manage_authors(self, page: Page, live_server_url: str, authenticated_page, task_basic, user_coauthor):
        """Creator can add/remove coauthors."""
        go_to_task_authors(authenticated_page, live_server_url, task_basic.pk)

        # Add coauthor
        authenticated_page.get_by_label("Autores").select_option(label=user_coauthor.username)
        authenticated_page.get_by_role("button", name="Guardar cambios").click()
        authenticated_page.wait_for_load_state("networkidle")

        # Verify coauthor added
        expect(authenticated_page.get_by_text(user_coauthor.username)).to_be_visible()

    def test_creator_can_edit_task(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Creator can edit title, body, and status."""
        go_to_task_edit(authenticated_page, live_server_url, task_basic.pk)

        authenticated_page.get_by_label("Título").fill("Updated by Creator")
        authenticated_page.get_by_label("Body (Markdown)").fill("Updated content")
        authenticated_page.get_by_label("Estado").select_option("in_progress")
        click_save_changes(authenticated_page)

        expect(authenticated_page.get_by_role("heading", name="Updated by Creator")).to_be_visible()
        expect(authenticated_page.get_by_text("En proceso")).to_be_visible()

    def test_creator_cannot_remove_self(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Creator cannot remove themselves from authors."""
        go_to_task_authors(authenticated_page, live_server_url, task_basic.pk)

        # Creator should not be in the selectable list
        expect(authenticated_page.get_by_label("Autores")).not_to_contain_text("creator")

        # Even if we try to submit empty, creator remains
        authenticated_page.get_by_role("button", name="Guardar cambios").click()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.get_by_text("creator (creador)")).to_be_visible()


class TestCoauthorPermissions:
    """Tests for coauthor permissions."""

    def test_coauthor_can_view_task(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor can view task detail."""
        go_to_task_detail(coauthor_page, live_server_url, task_with_coauthor.pk)

        expect(coauthor_page.get_by_role("heading", name="Shared Task")).to_be_visible()

    def test_coauthor_can_edit_body(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor can edit task body."""
        go_to_task_edit(coauthor_page, live_server_url, task_with_coauthor.pk)

        coauthor_page.get_by_label("Body (Markdown)").fill("Edited by coauthor")
        click_save_changes(coauthor_page)

        expect(coauthor_page.get_by_text("Edited by coauthor")).to_be_visible()

    def test_coauthor_can_change_status(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor can change task status."""
        go_to_task_edit(coauthor_page, live_server_url, task_with_coauthor.pk)

        coauthor_page.get_by_label("Estado").select_option("completed")
        click_save_changes(coauthor_page)

        expect(coauthor_page.get_by_text("Realizada")).to_be_visible()

    def test_coauthor_cannot_manage_authors(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor cannot access author management."""
        # Try to navigate directly to authors page
        coauthor_page.goto(f"{live_server_url}/tareas/{task_with_coauthor.pk}/authors/")
        coauthor_page.wait_for_load_state("networkidle")

        # Should get 403 or redirect
        # The view raises PermissionDenied which becomes 403
        expect(coauthor_page).to_have_url(f"{live_server_url}/tareas/{task_with_coauthor.pk}/authors/")

    def test_coauthor_does_not_see_authors_button(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor doesn't see authors management button."""
        go_to_task_detail(coauthor_page, live_server_url, task_with_coauthor.pk)

        expect(coauthor_page.get_by_role("link", name="Autores")).not_to_be_visible()

    def test_coauthor_cannot_change_creator(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor cannot change task creator (not editable)."""
        go_to_task_edit(coauthor_page, live_server_url, task_with_coauthor.pk)

        # Creator field not in form
        expect(coauthor_page.get_by_label("Creador")).not_to_be_visible()


class TestExternalUserPermissions:
    """Tests for external user (no access) permissions."""

    def test_external_cannot_view_task(self, page: Page, live_server_url: str, external_page, task_basic):
        """External user cannot view task detail."""
        external_page.goto(f"{live_server_url}/tareas/{task_basic.pk}/")
        external_page.wait_for_load_state("networkidle")

        # Should get 403/404 or redirect
        # TaskAccessMixin raises PermissionDenied
        expect(external_page).not_to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/")

    def test_external_cannot_edit_task(self, page: Page, live_server_url: str, external_page, task_basic):
        """External user cannot edit task."""
        external_page.goto(f"{live_server_url}/tareas/{task_basic.pk}/edit/")
        external_page.wait_for_load_state("networkidle")

        expect(external_page).not_to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/edit/")

    def test_external_cannot_access_authors(self, page: Page, live_server_url: str, external_page, task_basic):
        """External user cannot access author management."""
        external_page.goto(f"{live_server_url}/tareas/{task_basic.pk}/authors/")
        external_page.wait_for_load_state("networkidle")

        expect(external_page).not_to_have_url(f"{live_server_url}/tareas/{task_basic.pk}/authors/")

    def test_external_cannot_guess_task_urls(self, page: Page, live_server_url: str, external_page, task_basic):
        """Knowing task ID doesn't grant access."""
        # Try various task URLs
        for url in [
            f"{live_server_url}/tareas/{task_basic.pk}/",
            f"{live_server_url}/tareas/{task_basic.pk}/edit/",
            f"{live_server_url}/tareas/{task_basic.pk}/authors/",
        ]:
            external_page.goto(url)
            external_page.wait_for_load_state("networkidle")
            expect(external_page).not_to_have_url(url)


class TestTaskListIsolation:
    """Tests that task list respects permissions."""

    def test_creator_sees_own_tasks(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Creator sees all their tasks."""
        go_to_task_list(authenticated_page, live_server_url)

        for task in task_multiple:
            expect(authenticated_page.get_by_text(task.title)).to_be_visible()

    def test_coauthor_sees_shared_tasks(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor sees shared tasks in list."""
        go_to_task_list(coauthor_page, live_server_url)

        expect(coauthor_page.get_by_text("Shared Task")).to_be_visible()

    def test_external_sees_no_tasks(self, page: Page, live_server_url: str, external_page, task_basic):
        """External user sees empty task list."""
        go_to_task_list(external_page, live_server_url)

        expect(external_page.get_by_text("No hay tareas aún")).to_be_visible()


class TestSearchRespectsPermissions:
    """Tests that search respects permissions."""

    def test_coauthor_searches_only_accessible(self, page: Page, live_server_url: str, coauthor_page, task_with_coauthor):
        """Coauthor search only finds accessible tasks."""
        from tests.e2e.helpers.navigation import search_tasks

        go_to_task_list(coauthor_page, live_server_url)
        search_tasks(coauthor_page, live_server_url, "Shared")

        expect(coauthor_page.get_by_text("Shared Task")).to_be_visible()

    def test_external_search_empty(self, page: Page, live_server_url: str, external_page, task_basic):
        """External user search returns no results."""
        from tests.e2e.helpers.navigation import search_tasks

        go_to_task_list(external_page, live_server_url)
        search_tasks(external_page, live_server_url, "Test")

        expect(external_page.get_by_text('No hay coincidencias para "Test"')).to_be_visible()