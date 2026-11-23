"""
Authentication helpers for E2E tests.

Provides reusable functions for login, logout, and registration flows.
"""
from playwright.sync_api import Page


def login(page: Page, live_server_url: str, username: str, password: str) -> None:
    """
    Log in a user via the login form.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        username: Username or email
        password: Password
    """
    page.goto(f"{live_server_url}/cuentas/login/")
    page.get_by_label("Usuario o correo electrónico").fill(username)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_role("button", name="Iniciar sesión").click()
    page.wait_for_url(f"{live_server_url}/cuentas/dashboard/")


def login_with_email(page: Page, live_server_url: str, email: str, password: str) -> None:
    """
    Log in using email instead of username.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        email: User's email
        password: Password
    """
    page.goto(f"{live_server_url}/cuentas/login/")
    page.get_by_label("Usuario o correo electrónico").fill(email)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_role("button", name="Iniciar sesión").click()
    page.wait_for_url(f"{live_server_url}/cuentas/dashboard/")


def logout(page: Page, live_server_url: str) -> None:
    """
    Log out the current user via POST.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
    """
    # Click user dropdown
    page.locator(".dropdown-toggle").click()
    # Click logout button in dropdown
    page.get_by_role("menuitem", name="Cerrar sesión").click()
    # Wait for redirect to login
    page.wait_for_url(f"{live_server_url}/cuentas/login/")


def register(page: Page, live_server_url: str, username: str, email: str, password: str, password_confirm: str = None) -> None:
    """
    Register a new user.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        username: Desired username
        email: Email address
        password: Password
        password_confirm: Password confirmation (defaults to password)
    """
    if password_confirm is None:
        password_confirm = password

    page.goto(f"{live_server_url}/cuentas/registro/")
    page.get_by_label("Nombre de usuario").fill(username)
    page.get_by_label("Correo electrónico").fill(email)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_label("Confirmar contraseña").fill(password_confirm)
    page.get_by_role("button", name="Registrarse").click()
    # Should redirect to login on success
    page.wait_for_url(f"{live_server_url}/cuentas/login/")


def register_expecting_error(page: Page, live_server_url: str, username: str, email: str, password: str, password_confirm: str = None):
    """
    Register a new user expecting validation errors.

    Returns the page so tests can check for error messages.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        username: Desired username
        email: Email address
        password: Password
        password_confirm: Password confirmation (defaults to password)
    """
    if password_confirm is None:
        password_confirm = password

    page.goto(f"{live_server_url}/cuentas/registro/")
    page.get_by_label("Nombre de usuario").fill(username)
    page.get_by_label("Correo electrónico").fill(email)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_label("Confirmar contraseña").fill(password_confirm)
    page.get_by_role("button", name="Registrarse").click()
    # Stay on registration page (errors)
    return page


def assert_logged_in(page: Page, live_server_url: str, username: str = None) -> None:
    """
    Assert that the user is logged in.

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
        username: Optional username to verify in the UI
    """
    # Check for user dropdown with username
    page.locator(".dropdown-toggle").click()
    if username:
        page.get_by_text(username).first.wait_for(state="visible")


def assert_logged_out(page: Page, live_server_url: str) -> None:
    """
    Assert that the user is logged out (on login page).

    Args:
        page: Playwright page object
        live_server_url: Base URL of the live server
    """
    page.wait_for_url(f"{live_server_url}/cuentas/login/")
    page.get_by_role("button", name="Iniciar sesión").wait_for(state="visible")