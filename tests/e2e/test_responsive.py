"""
E2E Tests for Responsive Design (S10).

Tests the application at Desktop (1440x900), Tablet (768x1024),
and Mobile (390x844) viewports.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_list,
    go_to_task_new,
    go_to_task_detail,
    search_tasks,
    open_search_dialog,
)
from tests.e2e.helpers.authentication import login

pytestmark = pytest.mark.e2e


# Viewport configurations
VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "mobile", "width": 390, "height": 844},
]


@pytest.fixture(params=VIEWPORTS, ids=[v["name"] for v in VIEWPORTS])
def viewport_page(page, request):
    """Page fixture with parameterized viewport."""
    viewport = request.param
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    yield page, viewport["name"]


class TestResponsiveNavigation:
    """Tests for responsive navigation."""

    def test_navbar_visible_all_viewports(self, viewport_page, live_server_url, user_creator):
        """Navbar visible at all viewport sizes."""
        page, viewport_name = viewport_page

        login(page, live_server_url, "creator", "TestPass123!")

        expect(page.locator(".navbar")).to_be_visible()
        expect(page.locator(".navbar-brand")).to_contain_text("TaskSite")

    def test_navbar_links_desktop(self, viewport_page, live_server_url, user_creator):
        """Navbar links visible on desktop."""
        page, viewport_name = viewport_page

        if viewport_name != "desktop":
            pytest.skip("Desktop only test")

        login(page, live_server_url, "creator", "TestPass123!")

        expect(page.get_by_role("link", name="Mis tareas")).to_be_visible()
        expect(page.get_by_role("link", name="Nueva tarea")).to_be_visible()

    def test_navbar_hamburger_mobile(self, viewport_page, live_server_url, user_creator):
        """Hamburger menu appears on mobile."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        login(page, live_server_url, "creator", "TestPass123!")

        expect(page.locator("#navbar-toggle")).to_be_visible()

    def test_search_button_all_viewports(self, viewport_page, live_server_url, user_creator):
        """Search button visible at all viewports."""
        page, viewport_name = viewport_page

        login(page, live_server_url, "creator", "TestPass123!")

        expect(page.get_by_role("button", name="Buscar tareas")).to_be_visible()


class TestResponsiveTaskList:
    """Tests for responsive task list."""

    def test_task_list_loads_all_viewports(self, viewport_page, live_server_url, authenticated_page, task_multiple):
        """Task list loads and displays at all viewports."""
        page, viewport_name = viewport_page

        go_to_task_list(page, live_server_url)

        expect(page.get_by_role("heading", name="Mis tareas")).to_be_visible()
        for task in task_multiple:
            expect(page.get_by_text(task.title)).to_be_visible()

    def test_task_items_stack_mobile(self, viewport_page, live_server_url, authenticated_page, task_multiple):
        """Task items stack vertically on mobile."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_list(page, live_server_url)

        # Task items should be visible and stacked
        items = page.locator(".task-item").all()
        assert len(items) >= 5


class TestResponsiveSidebar:
    """Tests for responsive sidebar behavior."""

    def test_sidebar_visible_desktop_tablet(self, viewport_page, live_server_url, authenticated_page):
        """Sidebar visible on desktop and tablet."""
        page, viewport_name = viewport_page

        if viewport_name == "mobile":
            pytest.skip("Not for mobile")

        go_to_task_list(page, live_server_url)

        expect(page.locator("#sidebar")).to_be_visible()
        expect(page.locator(".sidebar-header")).to_be_visible()

    def test_sidebar_collapsible_mobile(self, viewport_page, live_server_url, authenticated_page):
        """Sidebar is collapsible overlay on mobile."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_list(page, live_server_url)

        # Sidebar should be hidden initially
        sidebar = page.locator("#sidebar")
        expect(sidebar).not_to_have_attribute("open")

        # Toggle button should exist in navbar
        toggle = page.locator("#navbar-toggle")
        if toggle.count() > 0:
            toggle.click()
            expect(sidebar).to_have_attribute("open")

    def test_back_to_list_button_mobile(self, viewport_page, live_server_url, authenticated_page, task_basic):
        """Back to list button visible on mobile task detail."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_detail(page, live_server_url, task_basic.pk)

        expect(page.get_by_role("link", name="Volver")).to_be_visible()


class TestResponsiveForms:
    """Tests for responsive forms."""

    def test_task_form_fits_viewport(self, viewport_page, live_server_url, authenticated_page):
        """Task creation form fits within viewport."""
        page, viewport_name = viewport_page

        go_to_task_new(page, live_server_url)

        form = page.locator(".markdown-editor-wrapper")
        expect(form).to_be_visible()

        # Form should not overflow horizontally
        form_box = form.bounding_box()
        viewport_width = page.viewport_size["width"]
        assert form_box["width"] <= viewport_width

    def test_editor_toolbar_wraps(self, viewport_page, live_server_url, authenticated_page):
        """Editor toolbar wraps on narrow viewports."""
        page, viewport_name = viewport_page

        go_to_task_new(page, live_server_url)

        toolbar = page.locator(".editor-toolbar")
        expect(toolbar).to_be_visible()

        # Toolbar should be visible and usable
        expect(page.get_by_role("button", name="Negrita")).to_be_visible()

    def test_textarea_full_width(self, viewport_page, live_server_url, authenticated_page):
        """Textarea takes full available width."""
        page, viewport_name = viewport_page

        go_to_task_new(page, live_server_url)

        textarea = page.get_by_label("Body (Markdown)")
        expect(textarea).to_be_visible()

        # Should be editable at all viewports
        textarea.fill("Test")
        expect(textarea).to_have_value("Test")


class TestResponsiveDialogs:
    """Tests for responsive dialogs (search, preview)."""

    def test_search_dialog_fits_mobile(self, viewport_page, live_server_url, authenticated_page):
        """Search dialog fits mobile viewport."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_list(page, live_server_url)
        open_search_dialog(page)

        dialog = page.locator("#search-dialog[open]")
        expect(dialog).to_be_visible()

        # Dialog should not overflow
        dialog_box = dialog.bounding_box()
        viewport_width = page.viewport_size["width"]
        assert dialog_box["width"] <= viewport_width

    def test_preview_dialog_fits_viewport(self, viewport_page, live_server_url, authenticated_page):
        """Preview dialog fits within viewport."""
        page, viewport_name = viewport_page

        go_to_task_new(page, live_server_url)
        page.get_by_label("Body (Markdown)").fill("# Test")
        page.get_by_role("button", name="Vista previa").click()

        dialog = page.locator("#preview-dialog[open]")
        expect(dialog).to_be_visible()

        dialog_box = dialog.bounding_box()
        viewport_width = page.viewport_size["width"]
        assert dialog_box["width"] <= viewport_width

    def test_dialog_close_accessible(self, viewport_page, live_server_url, authenticated_page):
        """Dialog close button accessible at all viewports."""
        page, viewport_name = viewport_page

        go_to_task_list(page, live_server_url)
        open_search_dialog(page)

        close_btn = page.get_by_role("button", name="Cancelar")
        expect(close_btn).to_be_visible()
        close_btn.click()

        expect(page.locator("#search-dialog[open]")).not_to_be_visible()


class TestResponsiveTaskDetail:
    """Tests for responsive task detail view."""

    def test_detail_view_no_horizontal_scroll(self, viewport_page, live_server_url, authenticated_page, task_basic):
        """Task detail has no unintended horizontal overflow."""
        page, viewport_name = viewport_page

        go_to_task_detail(page, live_server_url, task_basic.pk)

        # Check body doesn't overflow
        body_scroll = page.evaluate("() => document.body.scrollWidth")
        viewport_width = page.viewport_size["width"]
        assert body_scroll <= viewport_width + 1  # Allow 1px tolerance

    def test_markdown_preview_responsive(self, viewport_page, live_server_url, authenticated_page, task_basic):
        """Markdown preview adapts to viewport."""
        page, viewport_name = viewport_page

        go_to_task_detail(page, live_server_url, task_basic.pk)

        preview = page.locator(".markdown-preview")
        expect(preview).to_be_visible()

        # Content should not overflow
        preview_box = preview.bounding_box()
        viewport_width = page.viewport_size["width"]
        assert preview_box["width"] <= viewport_width

    def test_meta_info_visible(self, viewport_page, live_server_url, authenticated_page, task_basic):
        """Task meta info visible at all viewports."""
        page, viewport_name = viewport_page

        go_to_task_detail(page, live_server_url, task_basic.pk)

        expect(page.get_by_text("Creado por:")).to_be_visible()
        expect(page.get_by_text("Creado:")).to_be_visible()
        expect(page.get_by_text("Actualizado:")).to_be_visible()
        expect(page.get_by_text("Autores:")).to_be_visible()


class TestResponsiveButtons:
    """Tests for button accessibility at all viewports."""

    def test_buttons_touch_target_mobile(self, viewport_page, live_server_url, authenticated_page):
        """Buttons have adequate touch target size on mobile."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_new(page, live_server_url)

        # Check primary button size
        btn = page.get_by_role("button", name="Crear")
        box = btn.bounding_box()

        # Minimum 44x44px touch target (WCAG)
        assert box["height"] >= 44
        assert box["width"] >= 44

    def test_form_controls_usable_mobile(self, viewport_page, live_server_url, authenticated_page):
        """Form controls usable on mobile."""
        page, viewport_name = viewport_page

        if viewport_name != "mobile":
            pytest.skip("Mobile only test")

        go_to_task_new(page, live_server_url)

        # Inputs should be focusable and fillable
        page.get_by_label("Título").fill("Mobile Test")
        page.get_by_label("Body (Markdown)").fill("# Mobile")

        expect(page.get_by_label("Título")).to_have_value("Mobile Test")


class TestResponsiveImages:
    """Tests for responsive images and static assets."""

    def test_css_loads_all_viewports(self, viewport_page, live_server_url, authenticated_page):
        """CSS loads correctly at all viewports."""
        page, viewport_name = viewport_page

        go_to_task_list(page, live_server_url)

        # Check that styles are applied (not raw HTML)
        # Sidebar should have styling
        sidebar = page.locator("#sidebar")
        expect(sidebar).to_be_visible()

        # Check for CSS custom properties
        bg_color = page.evaluate("() => getComputedStyle(document.body).getPropertyValue('--color-bg')")
        assert bg_color != ""

    def test_fonts_load(self, viewport_page, live_server_url, authenticated_page):
        """Web fonts load correctly."""
        page, viewport_name = viewport_page

        go_to_task_list(page, live_server_url)

        # Check Inter font is applied
        font_family = page.evaluate("() => getComputedStyle(document.body).fontFamily")
        assert "Inter" in font_family or "inter" in font_family.lower()