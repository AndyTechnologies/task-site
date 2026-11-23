"""
Navigation helpers for E2E tests.

Provides reusable functions for navigating the application.
"""
from playwright.sync_api import Page


def go_to_task_list(page: Page, live_server_url: str) -> None:
    """Navigate to the task list page."""
    page.goto(f"{live_server_url}/tareas/")
    page.wait_for_load_state("networkidle")


def go_to_task_new(page: Page, live_server_url: str) -> None:
    """Navigate to the new task page."""
    page.goto(f"{live_server_url}/tareas/new/")
    page.wait_for_load_state("networkidle")


def go_to_task_detail(page: Page, live_server_url: str, task_pk: int) -> None:
    """Navigate to a task detail page."""
    page.goto(f"{live_server_url}/tareas/{task_pk}/")
    page.wait_for_load_state("networkidle")


def go_to_task_edit(page: Page, live_server_url: str, task_pk: int) -> None:
    """Navigate to the task edit page."""
    page.goto(f"{live_server_url}/tareas/{task_pk}/edit/")
    page.wait_for_load_state("networkidle")


def go_to_task_authors(page: Page, live_server_url: str, task_pk: int) -> None:
    """Navigate to the task authors management page."""
    page.goto(f"{live_server_url}/tareas/{task_pk}/authors/")
    page.wait_for_load_state("networkidle")


def search_tasks(page: Page, live_server_url: str, query: str) -> None:
    """
    Search for tasks using the search dialog.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        query: Search query string
    """
    # Open search dialog
    page.get_by_role("button", name="Buscar tareas").click()
    # Wait for dialog to open
    page.locator("#search-dialog[open]").wait_for(state="visible")
    # Fill search input
    search_input = page.get_by_label("Término de búsqueda")
    search_input.fill(query)
    # Submit search (Enter key or click search button)
    search_input.press("Enter")
    # Wait for results
    page.wait_for_load_state("networkidle")


def open_search_dialog(page: Page) -> None:
    """Open the search dialog without searching."""
    page.get_by_role("button", name="Buscar tareas").click()
    page.locator("#search-dialog[open]").wait_for(state="visible")


def close_search_dialog(page: Page) -> None:
    """Close the search dialog."""
    page.get_by_role("button", name="Cancelar").click()
    page.locator("#search-dialog[open]").wait_for(state="hidden")


def click_task_in_sidebar(page: Page, task_title: str) -> None:
    """Click a task in the sidebar by title."""
    page.get_by_role("link", name=task_title, exact=True).click()
    page.wait_for_load_state("networkidle")


def click_new_task_button(page: Page) -> None:
    """Click the 'Nueva tarea' button in the header."""
    page.get_by_role("link", name="Nueva tarea").click()
    page.wait_for_load_state("networkidle")


def click_edit_task_button(page: Page) -> None:
    """Click the 'Editar' button in task detail."""
    page.get_by_role("link", name="Editar").click()
    page.wait_for_load_state("networkidle")


def click_manage_authors_button(page: Page) -> None:
    """Click the 'Autores' button in task detail."""
    page.get_by_role("link", name="Autores").click()
    page.wait_for_load_state("networkidle")


def click_back_to_list(page: Page) -> None:
    """Click the 'Volver' or 'Volver a la tarea' link."""
    # Try different possible back links
    for name in ["Volver", "Volver a la tarea", "Volver a mis tareas"]:
        link = page.get_by_role("link", name=name)
        if link.count() > 0:
            link.click()
            page.wait_for_load_state("networkidle")
            return
    raise AssertionError("No back link found")


def click_save_task(page: Page) -> None:
    """Click the save/create task button."""
    page.get_by_role("button", name="Crear").click()
    page.wait_for_load_state("networkidle")


def click_save_changes(page: Page) -> None:
    """Click the 'Guardar cambios' button."""
    page.get_by_role("button", name="Guardar cambios").click()
    page.wait_for_load_state("networkidle")


def click_cancel(page: Page) -> None:
    """Click the cancel button."""
    page.get_by_role("link", name="Cancelar").click()
    page.wait_for_load_state("networkidle")


def open_preview_dialog(page: Page) -> None:
    """Open the Markdown preview dialog."""
    page.get_by_role("button", name="Vista previa").click()
    page.locator("#preview-dialog[open]").wait_for(state="visible")


def close_preview_dialog(page: Page) -> None:
    """Close the Markdown preview dialog."""
    page.get_by_role("button", name="Cerrar vista previa").click()
    page.locator("#preview-dialog[open]").wait_for(state="hidden")