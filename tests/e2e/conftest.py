"""
E2E test configuration and fixtures.

Provides browser, page, context, live_server, and user fixtures
for Playwright + pytest-django integration.
"""
import pytest
from django.contrib.auth import get_user_model
from pytest_django.live_server_helper import LiveServer

User = get_user_model()


# =============================================================================
# BROWSER FIXTURES (from pytest-playwright)
# =============================================================================

# browser, context, page are provided by pytest-playwright automatically
# No need to redefine them unless we want custom behavior


# =============================================================================
# DJANGO LIVE SERVER
# =============================================================================

@pytest.fixture(scope="session")
def live_server_url(live_server: LiveServer) -> str:
    """
    Return the live server URL for tests to use.

    The live_server fixture from pytest-django starts a real Django
    development server in a separate thread with a test database.
    """
    return live_server.url


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def user_creator(db) -> User:
    """Create a test user (creator)."""
    return User.objects.create_user(
        username="creator",
        email="creator@test.com",
        password="TestPass123!",
    )


@pytest.fixture
def user_coauthor(db) -> User:
    """Create a test user (coauthor)."""
    return User.objects.create_user(
        username="coauthor",
        email="coauthor@test.com",
        password="TestPass123!",
    )


@pytest.fixture
def user_external(db) -> User:
    """Create an external user (no access to tasks)."""
    return User.objects.create_user(
        username="external",
        email="external@test.com",
        password="TestPass123!",
    )


@pytest.fixture
def user_inactive(db) -> User:
    """Create an inactive user."""
    user = User.objects.create_user(
        username="inactive",
        email="inactive@test.com",
        password="TestPass123!",
    )
    user.is_active = False
    user.save()
    return user


# =============================================================================
# TASK FIXTURES
# =============================================================================

@pytest.fixture
def task_basic(db, user_creator) -> "Task":
    """Create a basic task owned by creator."""
    from tasksite.tasks.models import Task
    return Task.objects.create(
        title="Test Task",
        body="# Hello\n\nThis is a **test** task.",
        created_by=user_creator,
    )


@pytest.fixture
def task_with_coauthor(db, user_creator, user_coauthor) -> "Task":
    """Create a task with a coauthor."""
    from tasksite.tasks.models import Task
    task = Task.objects.create(
        title="Shared Task",
        body="## Shared\n\nContent for *coauthor*.",
        created_by=user_creator,
    )
    task.authors.add(user_coauthor)
    return task


@pytest.fixture
def task_multiple(db, user_creator, user_coauthor) -> "Task":
    """Create multiple tasks for list tests."""
    from tasksite.tasks.models import Task
    tasks = []
    for i in range(5):
        task = Task.objects.create(
            title=f"Task {i+1}",
            body=f"Body for task {i+1}",
            created_by=user_creator,
        )
        tasks.append(task)
    return tasks


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

def login_user(page, live_server_url: str, username: str, password: str) -> None:
    """
    Log in a user via the login form.

    Navigates to login page, fills form, submits, and waits for redirect.
    """
    page.goto(f"{live_server_url}/cuentas/login/")
    page.get_by_label("Usuario o correo electrónico").fill(username)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_role("button", name="Iniciar sesión").click()
    # Wait for redirect to dashboard (or tasks list)
    page.wait_for_url(f"{live_server_url}/cuentas/dashboard/")


def logout_user(page, live_server_url: str) -> None:
    """
    Log out the current user via POST.

    Uses the dropdown menu logout form.
    """
    # Click user dropdown
    page.locator(".dropdown-toggle").click()
    # Click logout button in dropdown
    page.get_by_role("menuitem", name="Cerrar sesión").click()
    # Wait for redirect to login
    page.wait_for_url(f"{live_server_url}/cuentas/login/")


# =============================================================================
# AUTHENTICATED PAGE FIXTURES
# =============================================================================

@pytest.fixture
def authenticated_page(page, live_server_url, user_creator):
    """A page fixture logged in as the creator user."""
    login_user(page, live_server_url, "creator", "TestPass123!")
    yield page


@pytest.fixture
def coauthor_page(page, live_server_url, user_coauthor):
    """A page fixture logged in as the coauthor user."""
    login_user(page, live_server_url, "coauthor", "TestPass123!")
    yield page


@pytest.fixture
def external_page(page, live_server_url, user_external):
    """A page fixture logged in as an external user."""
    login_user(page, live_server_url, "external", "TestPass123!")
    yield page


# =============================================================================
# PLAYWRIGHT CONFIGURATION
# =============================================================================

@pytest.fixture(scope="session")
def playwright_browser_type():
    """Specify which browser to use (chromium, firefox, webkit)."""
    return "chromium"


# =============================================================================
# VIEWPORT FIXTURES
# =============================================================================

@pytest.fixture(params=[
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "mobile", "width": 390, "height": 844},
])
def viewport_page(page, request):
    """Page fixture with parameterized viewport sizes."""
    viewport = request.param
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    yield page, viewport["name"]


# =============================================================================
# CLEANUP
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_page_state(page):
    """Reset page state between tests."""
    yield
    # Clear any dialogs, close modals, etc.
    try:
        page.evaluate("() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); }")
    except Exception:
        pass