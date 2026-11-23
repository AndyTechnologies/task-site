"""
E2E Tests for User Registration (S1).

Tests the complete registration flow including validation,
successful registration, and error cases.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.authentication import (
    register,
    register_expecting_error,
    assert_logged_out,
)


pytestmark = pytest.mark.e2e


class TestRegistrationPageLoads:
    """Tests that the registration page loads correctly."""

    def test_registration_page_loads(self, page: Page, live_server_url: str):
        """Registration page opens and displays all fields."""
        page.goto(f"{live_server_url}/cuentas/registro/")

        # Check page title
        expect(page).to_have_title("Registrarse - TaskSite")

        # Check all form fields are present with correct labels
        expect(page.get_by_label("Nombre de usuario")).to_be_visible()
        expect(page.get_by_label("Correo electrónico")).to_be_visible()
        expect(page.get_by_label("Contraseña")).to_be_visible()
        expect(page.get_by_label("Confirmar contraseña")).to_be_visible()

        # Check placeholders
        expect(page.get_by_label("Nombre de usuario")).to_have_attribute("placeholder", "usuario")
        expect(page.get_by_label("Correo electrónico")).to_have_attribute("placeholder", "correo@ejemplo.com")

        # Check submit button
        expect(page.get_by_role("button", name="Registrarse")).to_be_visible()

        # Check link to login
        expect(page.get_by_role("link", name="Iniciar sesión")).to_be_visible()


class TestRegistrationSuccess:
    """Tests for successful registration."""

    def test_register_new_user(self, page: Page, live_server_url: str):
        """Register a new user successfully."""
        register(page, live_server_url, "newuser", "newuser@test.com", "TestPass123!")

        # Should redirect to login page
        assert_logged_out(page, live_server_url)

        # Verify user can now log in
        page.get_by_label("Usuario o correo electrónico").fill("newuser")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Iniciar sesión").click()
        page.wait_for_url(f"{live_server_url}/cuentas/dashboard/")

        # Verify logged in
        page.locator(".dropdown-toggle").click()
        expect(page.get_by_text("newuser")).to_be_visible()

    def test_register_with_email_login(self, page: Page, live_server_url: str):
        """Register then log in using email."""
        register(page, live_server_url, "emaillogin", "emaillogin@test.com", "TestPass123!")

        # Log in with email
        page.get_by_label("Usuario o correo electrónico").fill("emaillogin@test.com")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Iniciar sesión").click()
        page.wait_for_url(f"{live_server_url}/cuentas/dashboard/")

        page.locator(".dropdown-toggle").click()
        expect(page.get_by_text("emaillogin")).to_be_visible()


class TestRegistrationValidationErrors:
    """Tests for registration validation errors."""

    def test_duplicate_username(self, page: Page, live_server_url: str, user_creator):
        """Registration fails with duplicate username."""
        register_expecting_error(page, live_server_url, "creator", "new@test.com", "TestPass123!")

        # Should stay on registration page
        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")

        # Check error message
        expect(page.get_by_text("Ya existe un usuario con este nombre de usuario.")).to_be_visible()

    def test_duplicate_email(self, page: Page, live_server_url: str, user_creator):
        """Registration fails with duplicate email (case insensitive)."""
        register_expecting_error(page, live_server_url, "newuser", "CREATOR@test.com", "TestPass123!")

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        expect(page.get_by_text("Ya existe un usuario con este correo electrónico.")).to_be_visible()

    def test_invalid_email_format(self, page: Page, live_server_url: str):
        """Registration fails with invalid email format."""
        register_expecting_error(page, live_server_url, "testuser", "not-an-email", "TestPass123!")

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        expect(page.get_by_text("Ingrese un correo electrónico válido.")).to_be_visible()

    def test_password_mismatch(self, page: Page, live_server_url: str):
        """Registration fails when passwords don't match."""
        register_expecting_error(page, live_server_url, "testuser", "test@test.com", "TestPass123!", "DifferentPass123!")

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        # Django's UserCreationForm validates password mismatch
        expect(page.get_by_text("Las dos contraseñas no coinciden.")).to_be_visible()

    def test_empty_username(self, page: Page, live_server_url: str):
        """Registration fails with empty username."""
        page.goto(f"{live_server_url}/cuentas/registro/")
        page.get_by_label("Correo electrónico").fill("test@test.com")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_label("Confirmar contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Registrarse").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        expect(page.get_by_text("El nombre de usuario es obligatorio.")).to_be_visible()

    def test_empty_email(self, page: Page, live_server_url: str):
        """Registration fails with empty email."""
        page.goto(f"{live_server_url}/cuentas/registro/")
        page.get_by_label("Nombre de usuario").fill("testuser")
        page.get_by_label("Contraseña").fill("TestPass123!")
        page.get_by_label("Confirmar contraseña").fill("TestPass123!")
        page.get_by_role("button", name="Registrarse").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        expect(page.get_by_text("El correo electrónico es obligatorio.")).to_be_visible()

    def test_empty_password(self, page: Page, live_server_url: str):
        """Registration fails with empty password."""
        page.goto(f"{live_server_url}/cuentas/registro/")
        page.get_by_label("Nombre de usuario").fill("testuser")
        page.get_by_label("Correo electrónico").fill("test@test.com")
        page.get_by_role("button", name="Registrarse").click()

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        # Django's UserCreationForm error for empty password
        expect(page.get_by_text("Este campo es obligatorio.")).to_be_visible()

    def test_weak_password(self, page: Page, live_server_url: str):
        """Registration fails with weak password."""
        register_expecting_error(page, live_server_url, "testuser", "test@test.com", "123")

        expect(page).to_have_url(f"{live_server_url}/cuentas/registro/")
        # Django password validators will show error
        error_text = page.locator(".errorlist").first
        expect(error_text).to_contain_text("contraseña")


class TestRegistrationAccessibility:
    """Tests for accessibility of registration form."""

    def test_form_labels_associated(self, page: Page, live_server_url: str):
        """All inputs have proper label associations."""
        page.goto(f"{live_server_url}/cuentas/registro/")

        # Check each input has an associated label
        username_input = page.get_by_label("Nombre de usuario")
        email_input = page.get_by_label("Correo electrónico")
        password1_input = page.get_by_label("Contraseña")
        password2_input = page.get_by_label("Confirmar contraseña")

        expect(username_input).to_be_visible()
        expect(email_input).to_be_visible()
        expect(password1_input).to_be_visible()
        expect(password2_input).to_be_visible()

    def test_required_fields_marked(self, page: Page, live_server_url: str):
        """Required fields are marked with asterisk."""
        page.goto(f"{live_server_url}/cuentas/registro/")

        # Check for required indicators (asterisks in labels)
        expect(page.locator("label:has-text('Nombre de usuario') >> .. >> span[aria-hidden='true']")).to_contain_text("*")
        expect(page.locator("label:has-text('Correo electrónico') >> .. >> span[aria-hidden='true']")).to_contain_text("*")
        expect(page.locator("label:has-text('Contraseña') >> .. >> span[aria-hidden='true']")).to_contain_text("*")
        expect(page.locator("label:has-text('Confirmar contraseña') >> .. >> span[aria-hidden='true']")).to_contain_text("*")

    def test_autocomplete_attributes(self, page: Page, live_server_url: str):
        """Fields have proper autocomplete attributes."""
        page.goto(f"{live_server_url}/cuentas/registro/")

        expect(page.get_by_label("Nombre de usuario")).to_have_attribute("autocomplete", "username")
        expect(page.get_by_label("Correo electrónico")).to_have_attribute("autocomplete", "email")
        expect(page.get_by_label("Contraseña")).to_have_attribute("autocomplete", "new-password")
        expect(page.get_by_label("Confirmar contraseña")).to_have_attribute("autocomplete", "new-password")