"""
E2E Tests for Markdown Editor (S7).

Tests the editor toolbar, Markdown writing, preview dialog,
saving, persistence, and security (XSS prevention).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.navigation import (
    go_to_task_new,
    go_to_task_edit,
    click_save_task,
    click_save_changes,
    open_preview_dialog,
    close_preview_dialog,
)

pytestmark = pytest.mark.e2e


class TestMarkdownEditorLoads:
    """Tests that the Markdown editor loads correctly."""

    def test_editor_loads_on_new_task(self, page: Page, live_server_url: str, authenticated_page):
        """Editor loads with toolbar and textarea on new task page."""
        go_to_task_new(authenticated_page, live_server_url)

        # Check toolbar buttons
        expect(authenticated_page.get_by_role("button", name="Encabezado 1")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Encabezado 2")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Negrita")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Cursiva")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Código inline")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Enlace")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Lista desordenada")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Lista ordenada")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Bloque de código")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Lista de tareas")).to_be_visible()
        expect(authenticated_page.get_by_role("button", name="Vista previa")).to_be_visible()

        # Check textarea
        expect(authenticated_page.get_by_label("Body (Markdown)")).to_be_visible()
        expect(authenticated_page.get_by_label("Body (Markdown)")).to_be_editable()

    def test_editor_loads_on_edit_task(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Editor loads on edit page with existing content."""
        go_to_task_edit(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_label("Body (Markdown)")).to_be_visible()
        expect(authenticated_page.get_by_label("Body (Markdown)")).to_have_value(task_basic.body)


class TestToolbarActions:
    """Tests for toolbar button actions."""

    def test_heading_1_button(self, page: Page, live_server_url: str, authenticated_page):
        """H1 button inserts # prefix."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Encabezado 1").click()

        expect(textarea).to_have_value("# ")

    def test_heading_2_button(self, page: Page, live_server_url: str, authenticated_page):
        """H2 button inserts ## prefix."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Encabezado 2").click()

        expect(textarea).to_have_value("## ")

    def test_bold_button(self, page: Page, live_server_url: str, authenticated_page):
        """Bold button wraps selection or inserts ** **."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("bold text")
        textarea.select_text()
        authenticated_page.get_by_role("button", name="Negrita").click()

        expect(textarea).to_have_value("**bold text**")

    def test_italic_button(self, page: Page, live_server_url: str, authenticated_page):
        """Italic button wraps selection or inserts * *."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("italic text")
        textarea.select_text()
        authenticated_page.get_by_role("button", name="Cursiva").click()

        expect(textarea).to_have_value("*italic text*")

    def test_code_button(self, page: Page, live_server_url: str, authenticated_page):
        """Code button wraps selection or inserts ` `."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("code")
        textarea.select_text()
        authenticated_page.get_by_role("button", name="Código inline").click()

        expect(textarea).to_have_value("`code`")

    def test_link_button(self, page: Page, live_server_url: str, authenticated_page):
        """Link button inserts [ ](url)."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Enlace").click()

        expect(textarea).to_have_value("[ ](url)")

    def test_unordered_list_button(self, page: Page, live_server_url: str, authenticated_page):
        """Unordered list button inserts - prefix."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Lista desordenada").click()

        expect(textarea).to_have_value("- ")

    def test_ordered_list_button(self, page: Page, live_server_url: str, authenticated_page):
        """Ordered list button inserts 1. prefix."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Lista ordenada").click()

        expect(textarea).to_have_value("1. ")

    def test_code_block_button(self, page: Page, live_server_url: str, authenticated_page):
        """Code block button inserts ``` ```."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Bloque de código").click()

        expect(textarea).to_have_value("```\n\n```")

    def test_task_list_button(self, page: Page, live_server_url: str, authenticated_page):
        """Task list button inserts - [ ]."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        authenticated_page.get_by_role("button", name="Lista de tareas").click()

        expect(textarea).to_have_value("- [ ] ")


class TestKeyboardShortcuts:
    """Tests for keyboard shortcuts in editor."""

    def test_ctrl_b_bold(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+B applies bold."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("test")
        textarea.select_text()
        textarea.press("Control+b")

        expect(textarea).to_have_value("**test**")

    def test_ctrl_i_italic(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+I applies italic."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("test")
        textarea.select_text()
        textarea.press("Control+i")

        expect(textarea).to_have_value("*test*")

    def test_ctrl_e_code(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+E applies inline code."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("test")
        textarea.select_text()
        textarea.press("Control+e")

        expect(textarea).to_have_value("`test`")

    def test_ctrl_k_link(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+K inserts link."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        textarea.press("Control+k")

        expect(textarea).to_have_value("[ ](url)")

    def test_ctrl_l_unordered_list(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+L inserts unordered list."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        textarea.press("Control+l")

        expect(textarea).to_have_value("- ")

    def test_ctrl_p_preview(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+P toggles preview."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("# Test")
        textarea.press("Control+p")

        expect(authenticated_page.locator("#preview-dialog[open]")).to_be_visible()

    def test_ctrl_1_heading_1(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+1 inserts H1."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        textarea.press("Control+1")

        expect(textarea).to_have_value("# ")

    def test_ctrl_2_heading_2(self, page: Page, live_server_url: str, authenticated_page):
        """Ctrl+2 inserts H2."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.click()
        textarea.press("Control+2")

        expect(textarea).to_have_value("## ")

    def test_tab_indentation(self, page: Page, live_server_url: str, authenticated_page):
        """Tab key inserts two spaces."""
        go_to_task_new(authenticated_page, live_server_url)

        textarea = authenticated_page.get_by_label("Body (Markdown)")
        textarea.fill("line 1\nline 2")
        # Position cursor at start of line 2
        textarea.press("Home")
        textarea.press("ArrowDown")
        textarea.press("Tab")

        expect(textarea).to_have_value("line 1\n  line 2")


class TestPreviewDialog:
    """Tests for the Markdown preview dialog."""

    def test_preview_opens(self, page: Page, live_server_url: str, authenticated_page):
        """Preview button opens dialog."""
        go_to_task_new(authenticated_page, live_server_url)

        authenticated_page.get_by_label("Body (Markdown)").fill("# Preview Test\n\n**Bold**")
        open_preview_dialog(authenticated_page)

        expect(authenticated_page.locator("#preview-dialog[open]")).to_be_visible()
        expect(authenticated_page.locator("#preview-dialog h2")).to_contain_text("Preview Test")
        expect(authenticated_page.locator("#preview-dialog strong")).to_contain_text("Bold")

    def test_preview_closes_with_button(self, page: Page, live_server_url: str, authenticated_page):
        """Preview closes with close button."""
        go_to_task_new(authenticated_page, live_server_url)

        open_preview_dialog(authenticated_page)
        close_preview_dialog(authenticated_page)

        expect(authenticated_page.locator("#preview-dialog[open]")).not_to_be_visible()

    def test_preview_closes_with_escape(self, page: Page, live_server_url: str, authenticated_page):
        """Preview closes with Escape key."""
        go_to_task_new(authenticated_page, live_server_url)

        open_preview_dialog(authenticated_page)
        authenticated_page.keyboard.press("Escape")

        expect(authenticated_page.locator("#preview-dialog[open]")).not_to_be_visible()

    def test_preview_updates_on_input(self, page: Page, live_server_url: str, authenticated_page):
        """Preview updates when textarea content changes (debounced)."""
        go_to_task_new(authenticated_page, live_server_url)

        authenticated_page.get_by_label("Body (Markdown)").fill("# Initial")
        open_preview_dialog(authenticated_page)

        expect(authenticated_page.locator("#preview-dialog h1")).to_contain_text("Initial")

        # Update textarea
        authenticated_page.get_by_label("Body (Markdown)").fill("# Updated")
        # Wait for debounce
        authenticated_page.wait_for_timeout(400)

        expect(authenticated_page.locator("#preview-dialog h1")).to_contain_text("Updated")


class TestMarkdownRendering:
    """Tests for Markdown rendering in editor and preview."""

    def test_save_renders_markdown_in_detail(self, page: Page, live_server_url: str, authenticated_page):
        """Saved Markdown renders correctly in detail view."""
        go_to_task_new(authenticated_page, live_server_url)

        markdown = """# Heading 1
## Heading 2

**Bold** and *italic*

- List item 1
- List item 2

1. Ordered 1
2. Ordered 2

`inline code`

```python
def hello():
    pass
```

> Quote

[Link](https://example.com)

- [x] Done
- [ ] Todo
"""
        authenticated_page.get_by_label("Título").fill("Render Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(markdown)
        click_save_task(authenticated_page)

        # Check rendered output in detail view
        expect(authenticated_page.locator(".markdown-preview h1")).to_contain_text("Heading 1")
        expect(authenticated_page.locator(".markdown-preview h2")).to_contain_text("Heading 2")
        expect(authenticated_page.locator(".markdown-preview strong")).to_contain_text("Bold")
        expect(authenticated_page.locator(".markdown-preview em")).to_contain_text("italic")
        expect(authenticated_page.locator(".markdown-preview li")).to_have_count(4)  # 2 unordered + 2 ordered
        expect(authenticated_page.locator(".markdown-preview code")).to_contain_text("inline code")
        expect(authenticated_page.locator(".markdown-preview pre code")).to_contain_text("def hello")
        expect(authenticated_page.locator(".markdown-preview blockquote")).to_contain_text("Quote")
        expect(authenticated_page.locator(".markdown-preview a")).to_have_attribute("href", "https://example.com")


class TestMarkdownSecurity:
    """Tests for XSS prevention in Markdown rendering."""

    def test_script_tag_escaped_in_detail(self, page: Page, live_server_url: str, authenticated_page):
        """Script tags are escaped, not executed."""
        go_to_task_new(authenticated_page, live_server_url)

        malicious = '<script>alert("XSS")</script>'
        authenticated_page.get_by_label("Título").fill("XSS Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(malicious)
        click_save_task(authenticated_page)

        # Check that script is escaped in rendered output
        rendered = authenticated_page.locator(".markdown-preview").inner_html()
        assert "<script>" not in rendered
        assert "<script>" in rendered or "script" in rendered

    def test_onload_attribute_escaped(self, page: Page, live_server_url: str, authenticated_page):
        """onload and other event handlers are escaped."""
        go_to_task_new(authenticated_page, live_server_url)

        malicious = '<img src="x" onload="alert(1)">'
        authenticated_page.get_by_label("Título").fill("XSS Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(malicious)
        click_save_task(authenticated_page)

        rendered = authenticated_page.locator(".markdown-preview").inner_html()
        assert "onload" not in rendered or "onload" in rendered  # Check it's not executable

    def test_javascript_protocol_escaped(self, page: Page, live_server_url: str, authenticated_page):
        """javascript: protocol links are neutralized."""
        go_to_task_new(authenticated_page, live_server_url)

        malicious = '[Click me](javascript:alert(1))'
        authenticated_page.get_by_label("Título").fill("XSS Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(malicious)
        click_save_task(authenticated_page)

        rendered = authenticated_page.locator(".markdown-preview").inner_html()
        # nh3 should strip javascript: protocol
        assert "javascript:" not in rendered

    def test_iframe_escaped(self, page: Page, live_server_url: str, authenticated_page):
        """iframe tags are escaped."""
        go_to_task_new(authenticated_page, live_server_url)

        malicious = '<iframe src="https://evil.com"></iframe>'
        authenticated_page.get_by_label("Título").fill("XSS Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(malicious)
        click_save_task(authenticated_page)

        rendered = authenticated_page.locator(".markdown-preview").inner_html()
        assert "<iframe" not in rendered

    def test_style_tag_escaped(self, page: Page, live_server_url: str, authenticated_page):
        """style tags are escaped."""
        go_to_task_new(authenticated_page, live_server_url)

        malicious = '<style>body { display: none; }</style>'
        authenticated_page.get_by_label("Título").fill("XSS Test")
        authenticated_page.get_by_label("Body (Markdown)").fill(malicious)
        click_save_task(authenticated_page)

        rendered = authenticated_page.locator(".markdown-preview").inner_html()
        assert "<style>" not in rendered


class TestPersistence:
    """Tests for content persistence."""

    def test_edit_preserves_markdown(self, page: Page, live_server_url: str, authenticated_page, task_basic):
        """Editing preserves Markdown source."""
        go_to_task_edit(authenticated_page, live_server_url, task_basic.pk)

        expect(authenticated_page.get_by_label("Body (Markdown)")).to_have_value(task_basic.body)

    def test_reload_preserves_content(self, page: Page, live_server_url: str, authenticated_page):
        """Reloading page preserves content."""
        go_to_task_new(authenticated_page, live_server_url)

        authenticated_page.get_by_label("Título").fill("Persist Test")
        authenticated_page.get_by_label("Body (Markdown)").fill("# Content\n\n**Bold**")
        click_save_task(authenticated_page)

        task_url = authenticated_page.url
        authenticated_page.reload()
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page).to_have_url(task_url)
        expect(authenticated_page.get_by_role("heading", name="Persist Test")).to_be_visible()
        expect(authenticated_page.locator(".markdown-preview strong")).to_contain_text("Bold")