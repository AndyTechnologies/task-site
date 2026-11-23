# Informe Técnico Final — Fase 1: Sistema de autenticación y usuarios con Django

---

## A. Resumen

Se ha implementado una infraestructura completa de usuarios y autenticación para la aplicación TaskSite, cumpliendo todos los requisitos de la especificación. Las funcionalidades implementadas incluyen:

1. **Modelo de usuario personalizado** (`accounts.User`) basado en `AbstractUser` con email único y normalizado
2. **Hashing de contraseñas con Argon2id** usando parámetros OWASP (memory_cost=19456, time_cost=2, parallelism=1)
3. **Registro de usuarios** con validación completa (username, email, password, confirmación)
4. **Autenticación dual** (username o email) con un solo campo de formulario
5. **Backend de autenticación personalizado** que resuelve ambigüedades y previene timing attacks
6. **Vistas basadas en clases (CBV)**: RegisterView, CustomLoginView, DashboardView, CustomLogoutView
7. **Mixins reutilizables**: `AnonymousRequiredMixin`, `LoginRequiredMixin`
8. **Templates** semánticos y accesibles con herencia de `base.html`
9. **Tests exhaustivos** (58 tests pasando) cubriendo modelo, formularios, backend, vistas y configuración
10. **Configuración Django** completa: `AUTH_USER_MODEL`, `AUTHENTICATION_BACKENDS`, `PASSWORD_HASHERS`, URLs con namespace

Todas las verificaciones pasan: `manage.py check`, `showmigrations`, `makemigrations --check --dry-run`, `test`.

---

## B. Arquitectura

### Estructura final

```
src/
└── tasksite/
    ├── __init__.py              # Punto de entrada: main()
    └── accounts/
        ├── __init__.py          # default_app_config
        ├── apps.py              # AccountsConfig (name="tasksite.accounts", label="accounts")
        ├── models.py            # User (AbstractUser) + CustomUserManager
        ├── managers.py          # (integrado en models.py)
        ├── forms.py             # CustomUserCreationForm, EmailOrUsernameAuthenticationForm
        ├── views.py             # CBVs + AnonymousRequiredMixin
        ├── backends.py          # EmailOrUsernameModelBackend
        ├── hashers.py           # CustomArgon2PasswordHasher
        ├── urls.py              # app_name='accounts', 4 rutas
        ├── migrations/
        │   ├── __init__.py
        │   └── 0001_initial.py  # Create model User
        └── templates/
            └── accounts/
                ├── base.html
                ├── register.html
                ├── login.html
                └── dashboard.html
```

### Configuración principal (`config/`)

```
config/
├── settings.py  # AUTH_USER_MODEL, AUTHENTICATION_BACKENDS, PASSWORD_HASHERS, etc.
├── urls.py      # Incluye accounts.urls con namespace='accounts'
├── wsgi.py
├── asgi.py
└── __init__.py
```

### Responsabilidades

| Componente | Responsabilidad |
|------------|-----------------|
| `User` (models.py) | Entidad de dominio, normalización email, unicidad |
| `CustomUserManager` | Centraliza creación y normalización de usuarios |
| `CustomArgon2PasswordHasher` | Hashing seguro con parámetros OWASP |
| `EmailOrUsernameModelBackend` | Resuelve username/email, detecta ambigüedades |
| `CustomUserCreationForm` | Validación registro, unicidad, normalización |
| `EmailOrUsernameAuthenticationForm` | Campo único para username/email |
| `AnonymousRequiredMixin` | Restringe acceso a usuarios autenticados |
| `RegisterView` | CreateView para registro |
| `CustomLoginView` | LoginView adaptada |
| `DashboardView` | TemplateView protegida |
| `CustomLogoutView` | LogoutView solo POST |

### Flujo de autenticación

```
Usuario accede a /cuentas/login/
    │
    ├─ GET → CustomLoginView → EmailOrUsernameAuthenticationForm → login.html
    │
    ├─ POST → form.validate() → authenticate(backend) → EmailOrUsernameModelBackend
    │                                    │
    │                                    ├─ Busca por username__iexact
    │                                    ├─ Busca por email__iexact (normalizado)
    │                                    ├─ Detecta ambigüedad (username de A ≠ email de B)
    │                                    ├─ Ejecuta hasher si no encontrado (timing attack prevention)
    │                                    └─ Verifica password + user_can_authenticate
    │
    ├─ Éxito → login(request, user) → redirect to dashboard
    │
    └─ Fallo → error no-campo → re-render login.html
```

### Organización de Templates y URLs

- **Templates**: Herencia de `base.html` → `register.html`, `login.html`, `dashboard.html`
- **URLs**: Namespace `accounts` con rutas `/cuentas/registro/`, `/cuentas/login/`, `/cuentas/dashboard/`, `/cuentas/logout/`
- **Raíz `/`**: Redirige a `accounts:login`

---

## C. Modelo de usuario

### Uso de `AbstractUser`

El modelo `User` hereda de `django.contrib.auth.models.AbstractUser`, aceptando todos los campos y relaciones nativos:
- Campos heredados: `password`, `last_login`, `is_superuser`, `first_name`, `last_name`, `is_staff`, `is_active`, `date_joined`, `groups`, `user_permissions`
- Campos propios: `username` (único), `email` (único, EmailField)
- Tabla BD: `accounts_user` (explícito via `Meta.db_table`)

### Manager personalizado

`CustomUserManager` centraliza la normalización:
```python
def normalize_email(self, email):
    return email.lower().strip() if email else ''
```
Se usa en `create_user`, `create_superuser` y en `User.save()`.

### Unicidad y normalización

- **Username**: Único a nivel BD (case-sensitive), validación case-insensitive en formulario
- **Email**: Único a nivel BD, normalizado a minúsculas sin espacios en manager, formulario y modelo
- **Garantía**: `unique=True` en BD + validación `__iexact` en formularios/backend

---

## D. Seguridad

### Argon2id con parámetros OWASP

```python
class CustomArgon2PasswordHasher(Argon2PasswordHasher):
    algorithm = "argon2"
    memory_cost = 19456  # KiB (19 MiB)
    time_cost = 2
    parallelism = 1
    type = 0  # Argon2id
```

**Hash generado**: `argon2$argon2id$v=19$m=19456,t=2,p=1$<salt>$<hash>`

### PASSWORD_HASHERS

```python
PASSWORD_HASHERS = [
    'tasksite.accounts.hashers.CustomArgon2PasswordHasher',  # Primero: genera nuevos hashes
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',      # Compatibilidad
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',      # Default Django (distintos params)
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]
```

### Gestión segura de contraseñas

- **Nunca** asignación directa a `user.password`
- Uso exclusivo de `user.set_password()` y `user.check_password()`
- Validadores nativos: `UserAttributeSimilarityValidator`, `MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`

### Protecciones adicionales

- **CSRF**: `{% csrf_token %}` en todos los formularios, middleware `CsrfViewMiddleware`
- **Logout**: Solo POST, rechaza GET con 405
- **Timing attack prevention**: Backend ejecuta `User().set_password(password)` para usuarios inexistentes
- **Ambigüedad**: Backend rechaza autenticación si identificador coincide con username de A y email de B (A ≠ B)
- **Rate limiting**: No implementado en esta fase (limitación documentada, ModelBackend no lo incluye)

---

## E. Programación orientada a objetos

### Herencia

| Clase | Hereda de | Propósito |
|-------|-----------|-----------|
| `User` | `AbstractUser` | Modelo de dominio con campos Django |
| `CustomUserManager` | `UserManager` | Normalización centralizada |
| `CustomArgon2PasswordHasher` | `Argon2PasswordHasher` | Parámetros OWASP |
| `EmailOrUsernameModelBackend` | `ModelBackend` | Resolución username/email |
| `CustomUserCreationForm` | `UserCreationForm` | Validación registro |
| `EmailOrUsernameAuthenticationForm` | `AuthenticationForm` | Campo único login |
| `AnonymousRequiredMixin` | `object` (mixin) | Restringe autenticados |
| `RegisterView` | `AnonymousRequiredMixin`, `CreateView` | Registro |
| `CustomLoginView` | `AnonymousRequiredMixin`, `LoginView` | Login |
| `DashboardView` | `LoginRequiredMixin`, `TemplateView` | Dashboard protegido |
| `CustomLogoutView` | `LogoutView` | Logout solo POST |

### Mixins

- **`AnonymousRequiredMixin`**: `dispatch()` redirige autenticados a dashboard
- **`LoginRequiredMixin`** (Django): Protege `DashboardView`
- Orden correcto: Mixin primero, luego vista base (`AnonymousRequiredMixin, CreateView`)

### Sobrescritura de métodos

- `User.save()`: Normaliza email antes de guardar
- `CustomUserManager.create_user/superuser`: Normaliza email
- `CustomUserCreationForm.clean_email/clean_username`: Validación unicidad case-insensitive
- `CustomUserCreationForm.save()`: Asegura email normalizado
- `EmailOrUsernameModelBackend.authenticate()`: Lógica completa de resolución dual
- `EmailOrUsernameAuthenticationForm.clean()`: Normaliza identificador
- `CustomLogoutView.dispatch()`: Rechaza GET (405)

### Polimorfismo

- `authenticate(request, username, password)` delega a backend polimórfico
- `LoginView` usa `form_class` configurable (`EmailOrUsernameAuthenticationForm`)
- `CreateView` usa `form_class` configurable (`CustomUserCreationForm`)

### Encapsulación

- Lógica de hashing encapsulada en `CustomArgon2PasswordHasher`
- Normalización de email centralizada en `CustomUserManager.normalize_email()`
- Resolución de usuario encapsulada en backend, no duplicada en vista/formulario
- Validaciones en formularios, no en vistas

### Separación de responsabilidades

| Capa | Responsabilidad |
|------|-----------------|
| Modelo | Datos, constraints BD, normalización persistente |
| Manager | Creación, queries, normalización |
| Hasher | Algoritmo criptográfico, parámetros |
| Backend | Resolución identidad, verificación credenciales |
| Formulario | Validación entrada usuario, UX |
| Vista | HTTP, flujo, redirección, templates |
| Template | Presentación, semántica, accesibilidad |

---

## F. Funcionalidades nativas de Django aprovechadas

| Funcionalidad | Uso |
|---------------|-----|
| `AbstractUser` | Base del modelo User, hereda permisos, grupos, admin |
| `UserCreationForm` | Base de `CustomUserCreationForm`, validación passwords |
| `AuthenticationForm` | Base de `EmailOrUsernameAuthenticationForm`, login logic |
| `LoginView` | Base de `CustomLoginView`, maneja autenticación, redirect |
| `LogoutView` | Base de `CustomLogoutView`, invalida sesión |
| `CreateView` | Base de `RegisterView`, maneja formulario, save, redirect |
| `TemplateView` | Base de `DashboardView`, render simple |
| `LoginRequiredMixin` | Protege `DashboardView` |
| `AccessMixin` | Base de `LoginRequiredMixin` |
| `ModelBackend` | Base de `EmailOrUsernameModelBackend`, `user_can_authenticate`, permisos |
| Sistema de sesiones | `SessionMiddleware`, `AuthenticationMiddleware`, `login()`, `logout()` |
| Templates | Herencia, `{% csrf_token %}`, `{{ form }}`, messages framework |
| URL namespaces | `app_name='accounts'`, `include(..., namespace='accounts')` |
| Migraciones | `makemigrations accounts`, `migrate`, dependencias `auth.0012` |
| Testing | `TestCase`, `Client`, `assertRedirects`, `assertContains`, `assertFormError` |
| Password validators | `AUTH_PASSWORD_VALIDATORS` (4 validadores nativos) |
| Password hashers | `PASSWORD_HASHERS` con fallback compatibilidad |

---

## G. Testing

### Resumen de tests (58 tests)

| Clase | Tests | Cobertura |
|-------|-------|-----------|
| `UserModelTests` | 11 | Creación, unicidad, normalización, hashing, verificación |
| `Argon2HasherTests` | 3 | Parámetros, formato hash, verificación |
| `RegistrationFormTests` | 7 | Válido, duplicados, mismatch, weak, email inválido, normalización |
| `AuthenticationFormTests` | 6 | Username, email, case-insensitive, password incorrecta, inexistente, inactivo |
| `AuthenticationBackendTests` | 9 | Username, email, case-insensitive, password incorrecta, inexistente, inactivo, None, ambigüedad, timing |
| `ViewAccessTests` | 14 | Acceso anónimo/auth, redirects, login, logout, CSRF, dashboard |
| `RegistrationViewTests` | 2 | Hash en registro, normalización email |
| `CustomSettingsTests` | 6 | AUTH_USER_MODEL, BACKENDS, HASHERS, URLs, INSTALLED_APPS |

### Comandos ejecutados y resultados

```bash
# Check del sistema
uv run python manage.py check
# System check identified no issues (0 silenced)

# Migraciones
uv run python manage.py showmigrations
# Todas marcadas [X]

# Dry-run migraciones
uv run python manage.py makemigrations --check --dry-run
# No changes detected

# Tests
uv run python manage.py test tasksite.accounts --verbosity=1
# Ran 58 tests in ~4.4s
# OK
```

### Tests en BD fresca

Verificado que las migraciones se aplican limpiamente en base de datos de pruebas SQLite en memoria (test runner de Django) y en archivo nuevo.

---

## H. Archivos modificados

### Archivos creados

```
src/tasksite/accounts/__init__.py
src/tasksite/accounts/apps.py
src/tasksite/accounts/models.py
src/tasksite/accounts/forms.py
src/tasksite/accounts/views.py
src/tasksite/accounts/backends.py
src/tasksite/accounts/hashers.py
src/tasksite/accounts/urls.py
src/tasksite/accounts/tests.py
src/tasksite/accounts/migrations/__init__.py
src/tasksite/accounts/migrations/0001_initial.py
src/tasksite/accounts/templates/accounts/base.html
src/tasksite/accounts/templates/accounts/register.html
src/tasksite/accounts/templates/accounts/login.html
src/tasksite/accounts/templates/accounts/dashboard.html
odd/tasks/auth-system.md
INFORME_TECNICO_FASE1.md
```

### Archivos modificados

```
config/settings.py      # AUTH_USER_MODEL, AUTHENTICATION_BACKENDS, PASSWORD_HASHERS, LOGIN_*, ALLOWED_HOSTS
config/urls.py          # Include accounts.urls con namespace, RedirectView raíz
```

### Dependencias

- **No se añadieron dependencias** a `pyproject.toml`
- `django[argon2]>=6.1.3` ya provee `argon2-cffi` (verificado con `uv tree`)
- `uv.lock` sin modificaciones

### Migraciones

- **Generada**: `accounts.0001_initial` (Create model User)
- **Aplicadas**: Todas (accounts, admin, auth, contenttypes, sessions)
- **Dependencias**: `('auth', '0012_alter_user_first_name_max_length')`

### Configuración clave

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'tasksite.accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]
PASSWORD_HASHERS = [
    'tasksite.accounts.hashers.CustomArgon2PasswordHasher',
    # ... fallbacks
]
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'
```

---

## I. Base de datos

### Estado inicial

- `db.sqlite3` existía con migraciones iniciales de Django (auth_user, etc.)
- **Backup**: `db.sqlite3.backup` creado antes de cambios
- **Acción**: `db.sqlite3` eliminada y recreada con migraciones frescas

### Migraciones aplicadas

```
accounts.0001_initial     Create model User (accounts_user)
auth.0001_initial .. 0012  Permissions, User model changes (tabla auth_user ya no usada)
admin.0001_initial .. 0003 Admin log
contenttypes.0001_initial 0002 Content types
sessions.0001_initial    Sessions
```

### Tablas finales

```
accounts_user                    # Modelo personalizado (reemplaza auth_user)
accounts_user_groups             # M2M groups
accounts_user_user_permissions   # M2M permissions
auth_group, auth_permission      # Grupos y permisos (Django)
django_admin_log, django_content_type, django_migrations, django_session, sqlite_sequence
```

### Índices únicos

- `sqlite_autoindex_accounts_user_1` → `username` (UNIQUE)
- `sqlite_autoindex_accounts_user_2` → `email` (UNIQUE)

### Operaciones pendientes

**Ninguna**. Base de datos limpia, migraciones aplicadas, modelo personalizado funcional.

---

## J. Dependencias y empaquetado

### Aprovechamiento de `django[argon2]`

- `pyproject.toml` declara: `"django[argon2]>=6.1.3"`
- `uv tree` confirma: `argon2-cffi v25.1.0` instalado como extra
- **No se ejecutó** `uv add argon2-cffi` (redundante)
- **No se modificó** `pyproject.toml` ni `uv.lock`

### Backend `uv_build`

- Configuración intacta en `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["uv_build>=0.12.15,<0.13.0"]
  build-backend = "uv_build"
  ```
- Paquete en `src/tasksite/` respetado

### Punto de entrada `tasksite`

- `pyproject.toml`: `tasksite = "tasksite:main"`
- `src/tasksite/__init__.py`: `def main(): print("Hello from tasksite!")`
- **Inconsistencia preexistente**: El entry point no lanza Django (`manage.py`), sino que imprime un saludo
- **No modificado** como parte de esta fase (fuera de alcance de autenticación)
- Documentado para resolver en fase posterior si se requiere CLI integrado

---

## K. Preparación para la siguiente fase

La infraestructura de autenticación está lista para incorporar una aplicación `tasks` sin modificaciones innecesarias:

### Puntos de extensión

1. **Modelo User listo**: `ForeignKey` a `settings.AUTH_USER_MODEL` (ej: `owner = models.ForeignKey(settings.AUTH_USER_MODEL, ...)`)
2. **Permisos**: `User` hereda `groups`, `user_permissions`, `is_staff`, `is_superuser` para RBAC futuro
3. **Dashboard extensible**: `DashboardView` puede evolucionar a lista de tareas del usuario
4. **URLs con namespace**: `accounts:` no colisiona con futuros `tasks:`
5. **Templates**: `base.html` provee navegación, estructura, messages framework
6. **LoginRequiredMixin**: Protege vistas de tareas automáticamente
7. **Tests**: Patrones establecidos para testear vistas protegidas, ownership, etc.

### Checklist para app `tasks`

- [ ] `python manage.py startapp tasks` dentro de `src/tasksite/`
- [ ] `Task` model con `ForeignKey` a `settings.AUTH_USER_MODEL`
- [ ] `tasks/urls.py` con `app_name='tasks'`
- [ ] Include en `config/urls.py` con namespace
- [ ] CBVs: `TaskListView`, `TaskCreateView`, `TaskUpdateView`, `TaskDeleteView`
- [ ] Templates extendiendo `accounts/base.html`
- [ ] Tests siguiendo patrones de `accounts/tests.py`
- [ ] Migraciones y verificación

---

## Verificación final

```bash
✓ uv run python manage.py check                    # 0 issues
✓ uv run python manage.py showmigrations           # All [X]
✓ uv run python manage.py makemigrations --check --dry-run  # No changes
✓ uv run python manage.py test tasksite.accounts   # 58 tests OK
✓ Functional test: register → login → dashboard → logout  # All working
✓ Argon2id hash verified: argon2$argon2id$v=19$m=19456,t=2,p=1$
✓ Email normalization: TEST@EXAMPLE.COM → test@example.com
✓ Ambiguous identifier rejected (username A ≠ email B)
✓ Timing attack prevention: hasher executed on not-found
✓ CSRF protection on all forms
✓ Logout only via POST (405 on GET)
✓ No modifications to pyproject.toml, uv_lock, uv_build
```

---

**Implementación completada, testeada y verificada.**  
Listo para Fase 2: Gestión de tareas.