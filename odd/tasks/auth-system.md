# Fase 1 — Sistema de autenticación y usuarios con Django

## Specs

### S1: Configuración del proyecto
El proyecto utiliza uv como gestor de dependencias, uv_build como backend de construcción, Python >= 3.12, Django >= 6.1.3 con extra argon2, SQLite como base de datos. El paquete principal está en `src/tasksite/`. El punto de entrada `tasksite = "tasksite:main"` existe en `src/tasksite/__init__.py`.

### S2: Modelo de usuario personalizado
Utilizar `AbstractUser` como base. Campos requeridos: username (único), email (único, normalizado), password (heredado, hashing Argon2id). Configurar `AUTH_USER_MODEL = "accounts.User"`.

### S3: Hashing de contraseñas con Argon2id
Usar `django.contrib.auth.hashers.Argon2PasswordHasher` con parámetros OWASP: memory_cost=19456, time_cost=2, parallelism=1. Crear `CustomArgon2PasswordHasher` en `tasksite.accounts.hashers`. Configurar `PASSWORD_HASHERS` con el hasher personalizado en primera posición.

### S4: Registro de usuarios
Usar `UserCreationForm` adaptado al modelo personalizado. Campos: username, email, password1, password2. Validaciones: unicidad username/email, validación email, validación contraseñas Django, coincidencia password1/password2. Redirigir a login tras registro exitoso. No iniciar sesión automáticamente.

### S5: Autenticación username o email
Formulario con campo único "Username o correo electrónico". Backend personalizado heredando de `ModelBackend` que resuelva usuario por username o email. Usar `authenticate()` y `login()`. Registrar en `AUTHENTICATION_BACKENDS`.

### S6: Vistas basadas en clases
- Registro: `CreateView`
- Login: `LoginView`
- Dashboard: `TemplateView` protegida con `LoginRequiredMixin`
- Logout: `LogoutView` (POST, CSRF, redirige a login)
Mixin reutilizable para restringir acceso a usuarios autenticados en registro/login.

### S7: Templates
- `base.html` compartida con HTML semántico, formularios accesibles, `{% csrf_token %}`, navegación según estado auth
- `accounts/register.html`: formulario registro + enlace login
- `accounts/login.html`: formulario login (username/email + password) + enlace registro
- `accounts/dashboard.html`: "Bienvenido, {username}" + botón logout POST

### S8: Configuración Django
Revisar/adaptar: `INSTALLED_APPS` (añadir accounts), `AUTH_USER_MODEL`, `AUTHENTICATION_BACKENDS`, `PASSWORD_HASHERS`, `AUTH_PASSWORD_VALIDATORS`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, `DATABASES` (SQLite), middlewares. Usar namespaces para URLs.

### S9: Testing obligatorio
- Modelo: creación, unicidad username/email, normalización email, hashing, verificación, parámetros Argon2id
- Registro: correcto, username duplicado, email duplicado, password inválida, confirmación incorrecta, persistencia
- Autenticación: login username, login email, login email normalizado, password incorrecta, usuario inexistente, usuario inactivo, sesión
- Acceso/logout: anon dashboard, auth dashboard, username visible, logout POST, rechazo GET, invalidación sesión, protección post-logout
- Checks: `manage.py check`, `showmigrations`, `makemigrations --check --dry-run`, `test`

## Tasks

| ID | Specs | Route | Commit |
|---|---|---|---|
| T1 | S1 | Create feature doc, inspect project state | feat: auth system - project inspection |
| T2 | S2 | Create accounts app: models.py, managers.py, apps.py | feat: auth system - custom user model |
| T3 | S3 | Create hashers.py with CustomArgon2PasswordHasher | feat: auth system - argon2id hasher |
| T4 | S5 | Create backends.py with EmailOrUsernameModelBackend | feat: auth system - auth backend |
| T5 | S4 | Create forms.py with CustomUserCreationForm, EmailOrUsernameAuthenticationForm | feat: auth system - forms |
| T6 | S6 | Create views.py with CBVs and mixins | feat: auth system - views |
| T7 | S8 | Update config/settings.py with all auth config | feat: auth system - settings |
| T8 | S8, S6 | Create accounts/urls.py, include in config/urls.py | feat: auth system - urls |
| T9 | S7 | Create templates: base.html, register.html, login.html, dashboard.html | feat: auth system - templates |
| T10 | S2, S8 | Backup db.sqlite3, recreate with fresh migrations | feat: auth system - migrations |
| T11 | S9 | Write tests in accounts/tests.py | feat: auth system - tests |
| T12 | S9 | Run all checks and verify | feat: auth system - verification |

## Log

L1: Inicio de implementación Fase 1 — Sistema de autenticación y usuarios con Django (request original verbatim)