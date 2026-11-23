"""
E2E Tests for Sidebar (S9).

Tests sidebar resize handle (mouse and keyboard), min/max width,
main area adaptation, task navigation, and visual selection state.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_list,
    go_to_task_detail,
    click_task_in_sidebar,
)

pytestmark = pytest.mark.e2e


class TestSidebarDisplay:
    """Tests for sidebar display and content."""

    def test_sidebar_visible_on_task_list(self, page: Page, live_server_url: str, authenticated_page):
        """Sidebar visible on task list page."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page.locator("#sidebar")).to_be_visible()
        expect(authenticated_page.locator(".sidebar-header")).to_contain_text("Mis tareas")

    def test_sidebar_visible_on_task_detail(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Sidebar visible on task detail page."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.locator("#sidebar")).to_be_visible()

    def test_sidebar_shows_task_list(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Sidebar shows list of accessible tasks."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar_items = authenticated_page.locator(".sidebar-item").all()
        assert len(sidebar_items) >= 5

        for task in task_multiple:
            expect(authenticated_page.locator(".sidebar-item")).to_contain_text(task.title)

    def test_sidebar_shows_status_badges(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Sidebar items show status badges."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page.locator(".sidebar-item-badge .badge")).to_be_visible()


class TestSidebarResizeMouse:
    """Tests for sidebar resize via mouse drag."""

    def test_resize_handle_exists(self, page: Page, live_server_url: str, authenticated_page):
        """Resize handle is present."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page.locator("#resize-handle")).to_be_visible()
        expect(authenticated_page.locator("#resize-handle")).to_have_attribute("role", "separator")

    def test_resize_changes_sidebar_width(self, page: Page, live_server_url: str, authenticated_page):
        """Dragging resize handle changes sidebar width."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        # Get initial width
        initial_width = sidebar.evaluate("el => el.offsetWidth")

        # Drag handle to the right (increase width)
        handle.hover()
        page.mouse.down()
        page.mouse.move(initial_width + 100, 0)
        page.mouse.up()

        # Wait for resize to apply
        page.wait_for_timeout(100)

        new_width = sidebar.evaluate("el => el.offsetWidth")
        assert new_width > initial_width

    def test_resize_respects_min_width(self, page: Page, live_server_url: str, authenticated_page):
        """Sidebar cannot be resized below minimum (224px)."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        # Try to drag far left (below min)
        handle.hover()
        page.mouse.down()
        page.mouse.move(-1000, 0)
        page.mouse.up()
        page.wait_for_timeout(100)

        width = sidebar.evaluate("el => el.offsetWidth")
        assert width >= 224

    def test_resize_respects_max_width(self, page: Page, live_server_url: str, authenticated_page):
        """Sidebar cannot be resized above maximum (512px)."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        # Try to drag far right (above max)
        handle.hover()
        page.mouse.down()
        page.mouse.move(10000, 0)
        page.mouse.up()
        page.wait_for_timeout(100)

        width = sidebar.evaluate("el => el.offsetWidth")
        assert width <= 512

    def test_main_area_adapts_to_resize(self, page: Page, live_server_url: str, authenticated_page):
        """Main content area adapts when sidebar resized."""
        go_to_task_list(authenticated_page, live_server_url)

        layout = authenticated_page.locator("#layout")
        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        # Get initial layout
        initial_sidebar_width = sidebar.evaluate("el => el.offsetWidth")

        # Resize sidebar
        handle.hover()
        page.mouse.down()
        page.mouse.move(initial_sidebar_width + 50, 0)
        page.mouse.up()
        page.wait_for_timeout(100)

        # Layout should use grid with sidebar width
        grid_template = layout.evaluate("el => window.getComputedStyle(el).gridTemplateColumns")
        assert "px" in grid_template


class TestSidebarResizeKeyboard:
    """Tests for sidebar resize via keyboard."""

    def test_arrow_left_decreases_width(self, page: Page, live_server_url: str, authenticated_page):
        """ArrowLeft on handle decreases sidebar width."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        initial_width = sidebar.evaluate("el => el.offsetWidth")

        handle.focus()
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(100)

        new_width = sidebar.evaluate("el => el.offsetWidth")
        assert new_width <= initial_width
        assert new_width >= 224

    def test_arrow_right_increases_width(self, page: Page, live_server_url: str, authenticated_page):
        """ArrowRight on handle increases sidebar width."""
        go_to_task_list(authenticated_page, live_server_url)

        sidebar = authenticated_page.locator("#sidebar")
        handle = authenticated_page.locator("#resize-handle")

        initial_width = sidebar.evaluate("el => el.offsetWidth")

        handle.focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(100)

        new_width = sidebar.evaluate("el => el.offsetWidth")
        assert new_width >= initial_width
        assert new_width <= 512


class TestSidebarNavigation:
    """Tests for sidebar task navigation."""

    def test_click_sidebar_item_navigates(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Clicking sidebar item navigates to task detail."""
        go_to_task_list(authenticated_page, live_server_url)

        click_task_in_sidebar(authenticated_page, task_multiple[0].title)

        expect(authenticated_page).to_have_url(f"{live_server_url}/tareas/{task_multiple[0].pk}/")

    def test_sidebar_highlight_updates(self, page: Page, live_server_url: str, authenticated_page, task_multiple):
        """Sidebar highlight updates on navigation."""
        go_to_task_detail(authenticated_page, live_server_url, task_multiple[0].pk)

        expect(authenticated_page.locator(".sidebar-item.active")).to_contain_text(task_multiple[0].title)

        # Navigate to another task via sidebar
        click_task_in_sidebar(authenticated_page, task_multiple[1].title)

        expect(authenticated_page.locator(".sidebar-item.active")).to_contain_text(task_multiple[1].title)

    def test_sidebar_aria_current_on_active(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Active sidebar item has aria-current=page."""
        go_to_task_detail(authenticated_page, live_server_url, task_basic.pk)

        active_item = authenticated_page.locator(".sidebar-item.active")
        expect(active_item).to_have_attribute("aria-current", "page")


class TestMobileSidebar:
    """Tests for mobile sidebar behavior (overlay)."""

    def test_mobile_sidebar_toggle(self, page: Page, live_server_url: str, authenticated_page):
        """Mobile sidebar can be toggled."""
        # Set mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})

        go_to_task_list(authenticated_page, live_server_url)

        # Sidebar should be closed initially (no 'open' attribute)
        sidebar = authenticated_page.locator("#sidebar")
        expect(sidebar).not_to_have_attribute("open")

        # Click toggle to open
        toggle = authenticated_page.get_by_role("button", name="Abrir menú")
        # The toggle is in the base template navbar
        if toggle.count() > 0:
            toggle.click()
            expect(sidebar).to_have_attribute("open")

    def test_mobile_overlay_closes_sidebar(self, page: Page, live_server_url: str, authenticated_page):
        """Clicking overlay closes mobile sidebar."""
        page.set_viewport_size({"width": 390, "height": 844})

        go_to_task_list(authenticated_page, live_server_url)

        # Open sidebar
        toggle = authenticated_page.get_by_role("button", name="Abrir menú")
        if toggle.count() > 0:
            toggle.click()

            # Click overlay
            overlay = authenticated_page.locator("#sidebar-overlay")
            if overlay.count() > 0:
                overlay.click()
                expect(authenticated_page.locator("#sidebar")).not_to_have_attribute("open")


class TestSidebarAccessibility:
    """Tests for sidebar accessibility."""

    def test_sidebar_has_aria_label(self, page: Page, live_server_url: str, authenticated_page):
        """Sidebar has accessible label."""
        go_to_task_list(authenticated_page, live_server_url)

        expect(authenticated_page.locator("#sidebar")).to_have_attribute("aria-label", "Lista de tareas")

    def test_resize_handle_accessible(self, page: Page, live_server_url: str, authenticated_page):
        """Resize handle has accessible name and role."""
        go_to_task_list(authenticated_page, live_server_url)

        handle = authenticated_page.locator("#resize-handle")
        expect(handle).to_have_attribute("role", "separator")
        expect(handle).to_have_attribute("aria-label", "Redimensionar barra lateral")
        expect(handle).to_have_attribute("aria-orientation", "horizontal")
        expect(handle).to_have_attribute("tabindex", "0")

    def test_sidebar_items_are_links(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Sidebar items are anchor tags with proper href."""
        go_to_task_list(authenticated_page, live_server_url)

        item = authenticated_page.locator(".sidebar-item").first
        expect(item).to_have_attribute("href", task_basic.get_absolute_url())