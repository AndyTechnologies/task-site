"""
E2E Tests for Login and Logout (S2).

Tests authentication flows including login with username/email,
failed attempts, session persistence, and logout.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.authentication import (
    login,
    login_with_email,
    logout,
    assert_logged_in,
    assert_logged_out,
)

pytestmark = pytest.mark.e2e


class TestLoginPageLoads:
    """Tests that the login page loads correctly."""

    def test_login_page_loads(self, page: Page, live_server_url: str):
        """Login page opens and displays all fields."""
        page.goto(f"{live_server_url}/cuentas/login/")

        expect(page).to_have_title("Iniciar sesión - TaskSite")

        # Check form fields
        expect(page.get_by_label("Usuario o correo electrónico")).to_be_visible()
        expect(page.get_by_label("Contraseña")).to_be_visible()
        expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()

        # Check placeholder
        expect(page.get_by_label("Usuario o correo electrónico")).to_have_attribute("placeholder", "usuario o correo@ejemplo.com")

        # Check link to register
        expect(page.get_by_role("link", name="Regístrate")).to_be_visible()

        # Check autofocus on username field
        expect(page.get_by_label("Usuario o correo electrónico")).to_be_focused()


class TestLoginSuccess:
    """Tests for successful login."""

    def test_login_with_username(self, page: Page, live_server_url: str, user_creator):
        """Log in using username."""
        login(page, live_server_url, "creator", "TestPass123!")

        assert_logged_in(page, live_server_url, "creator")

        # Should be on dashboard
        expect(page).to_have_url(f"{live_server_url}/cuentas/dashboard/")

    def test_login_with_email(self, page: Page, live_server_url: str, user_creator):
        """Log in using email address."""
        login_with_email(page, live_server_url, "creator@test.com", "TestPass123!")

        assert_logged_in(page, live_server_url, "creator")

    def test_login_redirects_to_tasks_list(self, page: Page, live_server_url: str, user_creator):
        """After login, user can access tasks."""
        login(page, live_server_url, "creator", "TestPass123!")

        # Navigate to tasks
        page.goto(f"{live_server_url}/tareas/")
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(f"{live_server_url}/tareas/")
        expect(page.get_by_role("heading", name="Mis tareas")).to_be_visible()


class TestLoginFailures:
    """Tests for failed login attempts."""

    def test_wrong_password(self, page: Page, live_server_url: str, user_creator):
        """Login fails with incorrect password."""
        page.goto(f"{live_server_url}/cuentas/login/")
        page.get_by_label("Usuario o correo electrónico").fill("creator")
        page.get_by_label("Contraseña").fill("WrongPassword123!")
        page.get_by_role("button", name="Iniciar sesión").click()

        # Should stay on login page
        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")

        # Check error message
        expect(page.get_by_text("Por favor, ingrese un usuario/correo y contraseña correctos.")).to_be_visible()

    def test_nonexistent_user(self, page: Page, live_server_url: str):
        """Login fails with nonexistent user."""
        page.goto(f"{live_server_url}/cuentas/login/")
        page.get_by_label("Usuario o correo electrónico").fill("nonexistent")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Iniciar sesión").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")
        expect(page.get_by_text("Por favor, ingrese un usuario/correo y contraseña correctos.")).to_be_visible()

    def test_inactive_user(self, page: Page, live_server_url: str, user_inactive):
        """Login fails for inactive user."""
        page.goto(f"{live_server_url}/cuentas/login/")
        page.get_by_label("Usuario o correo electrónico").fill("inactive")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Iniciar sesión").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")
        expect(page.get_by_text("Esta cuenta está inactiva.")).to_be_visible()

    def test_empty_username(self, page: Page, live_server_url: str):
        """Login fails with empty username."""
        page.goto(f"{live_server_url}/cuentas/login/")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Iniciar sesión").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")

    def test_empty_password(self, page: Page, live_server_url: str, user_creator):
        """Login fails with empty password."""
        page.goto(f"{live_server_url}/cuentas/login/")
        page.get_by_label("Usuario o correo electrónico").fill("creator")
        page.get_by_role("button", name="Iniciar sesión").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")


class TestSessionPersistence:
    """Tests for session persistence across page reloads."""

    def test_session_persists_after_reload(self, page: Page, live_server_url: str, user_creator):
        """Session persists after page reload."""
        login(page, live_server_url, "creator", "TestPass123!")

        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")

        # Should still be logged in (on dashboard)
        assert_logged_in(page, live_server_url, "creator")

    def test_session_persists_across_navigation(self, page: Page, live_server_url: str, user_creator):
        """Session persists when navigating between pages."""
        login(page, live_server_url, "creator", "TestPass123!")

        # Navigate to tasks
        page.goto(f"{live_server_url}/tareas/")
        page.wait_for_load_state("networkidle")

        # Go back to dashboard
        page.goto(f"{live_server_url}/cuentas/dashboard/")
        page.wait_for_load_state("networkidle")

        assert_logged_in(page, live_server_url, "creator")


class TestLogout:
    """Tests for logout functionality."""

    def test_logout_via_post(self, page: Page, live_server_url: str, user_creator):
        """Logout works via POST request."""
        login(page, live_server_url, "creator", "TestPass123!")

        logout(page, live_server_url)

        assert_logged_out(page, live_server_url)

    def test_logout_invalidates_session(self, page: Page, live_server_url: str, user_creator):
        """After logout, protected pages redirect to login."""
        login(page, live_server_url, "creator", "TestPass123!")
        logout(page, live_server_url)

        # Try to access protected page
        page.goto(f"{live_server_url}/tareas/")
        page.wait_for_load_state("networkidle")

        # Should redirect to login
        expect(page).to_have_url(f"{live_server_url}/cuentas/login/")

    def test_logout_from_dashboard(self, page: Page, live_server_url: str, user_creator):
        """Logout from dashboard page."""
        login(page, live_server_url, "creator", "TestPass123!")

        # Logout from dashboard using form
        page.locator('form[action*="logout"] button').click()
        page.wait_for_url(f"{live_server_url}/cuentas/login/")

        assert_logged_out(page, live_server_url)

    def test_logout_requires_post(self, page: Page, live_server_url: str, user_creator):
        """GET request to logout should be rejected."""
        login(page, live_server_url, "creator", "TestPass123!")

        # Try GET logout
        page.goto(f"{live_server_url}/cuentas/logout/")

        # Should return 405 Method Not Allowed or redirect
        # The view returns HttpResponseNotAllowed(['POST'])
        expect(page).to_have_url(f"{live_server_url}/cuentas/logout/")


class TestLoginAccessibility:
    """Tests for accessibility of login form."""

    def test_form_labels(self, page: Page, live_server_url: str):
        """Login form has proper labels."""
        page.goto(f"{live_server_url}/cuentas/login/")

        expect(page.get_by_label("Usuario o correo electrónico")).to_be_visible()
        expect(page.get_by_label("Contraseña")).to_be_visible()

    def test_autocomplete_attributes(self, page: Page, live_server_url: str):
        """Fields have proper autocomplete."""
        page.goto(f"{live_server_url}/cuentas/login/")

        expect(page.get_by_label("Usuario o correo electrónico")).to_have_attribute("autocomplete", "username")
        expect(page.get_by_label("Contraseña")).to_have_attribute("autocomplete", "current-password")

    def test_password_field_type(self, page: Page, live_server_url: str):
        """Password field is type password."""
        page.goto(f"{live_server_url}/cuentas/login/")

        expect(page.get_by_label("Contraseña")).to_have_attribute("type", "password")