# Feature — Browser E2E Testing

## Specs

**S1 — Registro de usuarios**
- Apertura de la página de registro
- Visualización correcta de todos los campos (username, email, password, confirm password)
- Labels y placeholders accesibles
- Introducción de username, email, contraseña, confirmación
- Envío del formulario
- Errores de validación: username duplicado, email duplicado, email mal formado, contraseña inválida, contraseñas diferentes, campos obligatorios
- Registro exitoso y redirección al login

**S2 — Login y logout**
- Login mediante username
- Login mediante email
- Contraseña incorrecta
- Usuario inexistente
- Usuario inactivo
- Redirecciones correctas
- Creación de sesión y persistencia al recargar
- Acceso a páginas protegidas tras login
- Logout mediante POST
- Invalidación de sesión y redirección tras logout

**S3 — Listado de tareas**
- Acceso autenticado
- Estado vacío (sin tareas)
- Visualización de tareas con títulos, estados
- Navegación hacia el detalle
- Orden esperado (por updated_at desc)
- Ausencia de tareas de usuarios ajenos

**S4 — Creación de tareas**
- Abrir el formulario de creación
- Introducir título
- Introducir body Markdown
- Seleccionar coautores
- Enviar el formulario
- Recibir confirmación y redirección al detalle
- Comprobar que los datos aparecen correctamente
- Recargar la página y verificar persistencia
- Errores de validación

**S5 — Búsqueda**
- Abrir el diálogo de búsqueda
- Foco inicial en el campo
- Escribir texto y buscar por título
- Buscar por contenido (body)
- Mostrar resultados
- Mostrar ausencia de resultados
- Conservar la búsqueda en la URL
- Limpiar la búsqueda
- Cerrar con Escape
- Restaurar el foco al control que abrió el diálogo

**S6 — Detalle de tarea**
- Apertura de una tarea
- Título, estado, creador, fecha creación, última modificación
- Autores con indicador de creador
- Navegación desde la sidebar
- Resaltado de la tarea seleccionada en sidebar
- Cambios de estado reflejados tras guardar

**S7 — Editor Markdown**
- Apertura del editor
- Escritura de Markdown
- Utilización de la toolbar: encabezados, negrita, cursiva, listas, enlaces, código, bloques de código, checkboxes
- Vista previa (diálogo)
- Guardado
- Indicador de guardado / mensajes de error
- Persistencia después de recargar
- **Seguridad**: contenido malicioso no ejecuta JavaScript en vista detallada (script tags, event handlers, protocolos peligrosos, HTML arbitrario)

**S8 — Permisos y colaboración**
- El creador puede gestionar coautores
- Un coautor puede visualizar la tarea
- Un coautor puede editar el body
- Un coautor puede modificar el estado
- Un coautor NO puede gestionar autores
- Un usuario externo no puede abrir la tarea
- Un usuario externo no puede editarla
- Los identificadores de tareas ajenas no permiten saltarse los permisos
- El creador original no puede eliminarse de authors

**S9 — Barra lateral**
- Redimensionamiento mediante ratón
- Anchura mínima (224px) y máxima (512px)
- Adaptación del área principal
- Redimensionamiento mediante teclado (ArrowLeft/ArrowRight)
- Navegación entre tareas
- Estado visual seleccionado

**S10 — Responsive**
- Viewports: Desktop (1440x900), Tablet (768x1024), Mobile (390x844)
- Navegación, Sidebar, Formularios, Diálogos, Listado, Editor Markdown, Botones
- Ausencia de desbordamiento horizontal no intencionado
- Accesibilidad de los controles en todos los viewports

## Tasks

| ID | Specs | Route | Commit |
|---|---|---|---|
| T1 | S1 | tests/e2e/test_registration.py |  |
| T2 | S2 | tests/e2e/test_login_logout.py |  |
| T3 | S3 | tests/e2e/test_task_list.py |  |
| T4 | S4 | tests/e2e/test_task_creation.py |  |
| T5 | S5 | tests/e2e/test_search.py |  |
| T6 | S6 | tests/e2e/test_task_detail.py |  |
| T7 | S7 | tests/e2e/test_markdown_editor.py |  |
| T8 | S8 | tests/e2e/test_permissions.py |  |
| T9 | S9 | tests/e2e/test_sidebar.py |  |
| T10 | S10 | tests/e2e/test_responsive.py |  |
| T11 | Infraestructura | tests/e2e/conftest.py, fixtures/, helpers/ |  |
| T12 | Configuración | pyproject.toml (pytest, markers) |  |
| T13 | CI/CD | .github/workflows/e2e.yml |  |
| T14 | Documentación | .gitignore, comandos de ejecución |  |

## Log

**L1** — User request: Implementar E2E testing con Playwright, pytest, Django y GitHub Actions (original request verbatim)

**L2** — Architecture decided: pytest + pytest-django + pytest-playwright, live_server fixture, Chromium headless, tests/e2e/ structure with conftest.py, fixtures/, helpers/, GitHub Actions workflow

**L3** — Dependencies to add: pytest, pytest-django, pytest-playwright (dev group via uv)