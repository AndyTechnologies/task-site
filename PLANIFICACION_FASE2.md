# Planificación Fase 2 — Tasks Core + Gentle-AI Design System

## Resumen ejecutivo

Esta fase implementa el núcleo funcional de gestión de tareas colaborativas y consolida la identidad visual de toda la aplicación bajo el sistema de diseño Gentle-AI. Incluye modelo de datos, permisos multiusuario, CRUD de tareas, búsqueda, editor Markdown seguro, y rediseño visual completo de autenticación y Tasks.

---

## A. Resumen funcional

**Objetivos:**
1. Modelo `Task` con relaciones M2M a usuarios (creador + autores)
2. Permisos estrictos: usuario solo ve tareas donde está en `authors`
3. CRUD completo: listado, creación, detalle, edición, gestión autores
4. Búsqueda full-text en título y body (Markdown)
5. Editor Markdown con toolbar, preview, sanitización XSS
6. Sidebar redimensionable en detalle
7. Sistema visual Gentle-AI unificado (accounts + tasks)
8. Tests exhaustivos (modelo, permisos, markdown, UI)

---

## B. Specs técnicos

| Spec | Descripción |
|---|---|
| **S1** | Modelo Task: id, title, body(MD), status(TextChoices), created_by(FK), authors(M2M), created_at, updated_at |
| **S2** | Creación: título, body opcional, coautores. Transacción atómica. Creador = request.user |
| **S3** | Permisos: QuerySet filtrado por `authors`. 404 en tareas ajenas. Autores editan body/estado. Solo creador gestiona autores. |
| **S4** | ListView principal: tareas accesibles, vertical, estado visible, empty state |
| **S5** | Búsqueda: `<dialog>` nativo, GET, Q(title\|body), filtrado por autores |
| **S6** | DetailView: layout 2 paneles (sidebar + main), sidebar redimensionable, metadatos |
| **S7** | Editor MD: toolbar, textarea mono, preview seguro, sanitización allowlist |
| **S8** | Metadatos: título, estado, creador, fechas, autores, coautores |
| **S9** | URLs namespace `tasks`: list, new, detail, edit, authors. LOGIN_REDIRECT_URL → tasks:list |
| **S10** | Arquitectura: ModelForms, CBVs, services.py, transacciones, mixins permisos |
| **S11** | Design System: tokens CSS, componentes compartidos, responsive, accesibilidad |
| **S12** | Testing: modelo, creación, permisos, markdown, UI (58+ tests) |
| **S13** | Migraciones aditivas para tasks, sin tocar accounts |

---

## C. Modelo de datos

```python
# tasksite/tasks/models.py
class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        IN_PROGRESS = "in_progress", "En proceso"
        COMPLETED = "completed", "Realizada"
        CANCELLED = "cancelled", "Cancelada"

    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tasks")
    authors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
```

**Reglas de negocio:**
- `created_by` ∈ `authors` siempre (auto al crear)
- `created_by` no removible de `authors`
- `created_by` inmutable
- Solo `created_by` puede añadir/quitar autores

---

## D. Permisos y aislamiento

| Operación | Quién | Validación |
|---|---|---|
| Listar | `user ∈ task.authors` | `get_queryset()` filtra |
| Ver detalle | `user ∈ task.authors` | `get_object()` + 404 |
| Editar body/estado | `user ∈ task.authors` | Form + view check |
| Gestionar autores | `user == task.created_by` | View check + form |
| Eliminar creador | **Nunca** | Model/Form validation |

**Implementación:** `TaskAccessMixin` con `get_queryset()` override + `dispatch()` checks.

---

## E. Arquitectura

### Estructura de archivos
```
src/tasksite/
├── tasks/
│   ├── __init__.py
│   ├── apps.py              # TasksConfig
│   ├── models.py            # Task, TaskManager
│   ├── forms.py             # TaskForm, TaskEditForm, AuthorForm
│   ├── views.py             # ListView, CreateView, DetailView, UpdateView, AuthorView
│   ├── services.py          # create_task, add_author, remove_author
│   ├── urls.py              # app_name='tasks'
│   ├── mixins.py            # TaskAccessMixin, CreatorRequiredMixin
│   ├── migrations/
│   ├── templates/tasks/
│   │   ├── base.html
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── form.html
│   │   ├── partials/
│   │   └── author_form.html
│   └── static/tasks/
│       ├── css/ (extends global)
│       └── js/ (editor, sidebar, search)
├── static/css/              # Design system global
│   ├── design-tokens.css
│   ├── global.css
│   ├── components.css
│   ├── layout.css
│   └── markdown.css
└── accounts/                # Actualización visual only
    └── templates/accounts/  # base.html, login.html, register.html (Gentle-AI)
```

### Servicios (`services.py`)
```python
def create_task(user, title, body, author_ids):
    with transaction.atomic():
        task = Task.objects.create(title=title, body=body, created_by=user)
        task.authors.add(user, *User.objects.filter(pk__in=author_ids, is_active=True))
    return task

def update_authors(task, user, author_ids):
    if user != task.created_by:
        raise PermissionDenied
    with transaction.atomic():
        current = set(task.authors.exclude(pk=task.created_by.pk).values_list('pk', flat=True))
        new = set(author_ids)
        task.authors.add(*User.objects.filter(pk__in=new - current, is_active=True))
        task.authors.remove(*(current - new))
```

---

## F. Gentle-AI Design System

### Skills utilizadas
- ✅ `gentle-ai-design/SKILL.md` — Tokens, paleta, tipografía, Tailwind v4 @theme
- ✅ `gentle-ui/SKILL.md` — Principios UX, componentes, responsive, accesibilidad

### Archivos creados
| Archivo | Propósito |
|---|---|
| `design/system.md` | Documentación completa del design system (actualizada con auditoría) |
| `src/tasksite/static/css/design-tokens.css` | CSS custom properties (tokens corregidos tras auditoría) |
| `src/tasksite/static/css/global.css` | Reset, base, utilities |
| `src/tasksite/static/css/components.css` | Botones, forms, cards, badges, messages, dropdowns (badges corregidos) |
| `src/tasksite/static/css/layout.css` | Navbar, sidebar, layout grid, dialogs, responsive |
| `src/tasksite/static/css/markdown.css` | Editor toolbar, textarea, preview, split view |
| `design/prototypes/login.html` | Prototipo login Gentle-AI |
| `design/prototypes/register.html` | Prototipo registro Gentle-AI |
| `design/prototypes/task-list.html` | Prototipo listado + search dialog |
| `design/prototypes/task-detail.html` | Prototipo detalle + sidebar resize |
| `design/prototypes/markdown-editor.html` | Prototipo editor + preview |

### Tokens principales (CSS custom properties) — auditados WCAG 2.1 AA
```css
:root {
  --color-bg: #09090b;           /* zinc-950 */
  --color-bg-card: #111113;      /* zinc-900 */
  --color-bg-code: #18181c;      /* zinc-950 darker */
  --color-border: #ffffff12;     /* 7% white */
  --color-border-hover: #ea188959; /* 35% magenta */
  --color-text: #fafafa;         /* zinc-50 */
  --color-text-muted: #a1a1aa;   /* zinc-400 */
  --color-text-tertiary: #a1a1aa; /* zinc-400 — corregido de #52525b para WCAG AA */
  --color-text-inverse: #09090b; /* para badges/btn-primary */
  --color-accent: #ea1889;       /* magenta-600 */
  --color-accent-hover: #ff6db0; /* magenta-400 */
  --color-accent-subtle: #ea188926; /* 15% */
  --color-error: #f43f5e;        /* rose-500 */
  --color-warning: #fbbf24;      /* amber-400 */
  --color-success: #34d399;      /* emerald-400 */
  --color-info: #ea1889;         /* magenta-600 */
}
```

**Auditoría de contraste (WCAG 2.1 AA):**
- Texto principal `#fafafa` on `#09090b`: 19.06:1 ✅
- Texto muted `#a1a1aa` on `#09090b`: 7.76:1 ✅
- **Texto tertiary `#a1a1aa` on `#09090b`: 7.76:1 ✅** (era `#52525b` = 2.57:1 ❌)
- Badges estado: texto `#09090b` on warning/success/error/info — todos ≥ 4.5:1 ✅
- `.btn-primary`: texto `#09090b` on acento `#ea1889`: 4.73:1 ✅
- Acento on card: 4.48:1 (solo large text)

### Decisión: CSS nativo vs Tailwind v4
**Elegido: CSS Custom Properties nativas**
- Razones: Proyecto Django simple, sin Node.js, sin build step frontend
- Tailwind v4 requiere PostCSS + proceso de build
- CSS custom properties dan misma funcionalidad de tokens sin dependencias
- Mantenimiento simple, cero tooling adicional

### Integración accounts + tasks
- `base.html` compartido (o extendido) carga: `global.css` + `components.css` + `layout.css`
- `tasks/base.html` añade: `markdown.css`
- Login/Registro actualizan visualmente: misma estructura, nuevos estilos Gentle-AI
- Comportamiento backend **inalterado**

---

## Dependencias a añadir en `pyproject.toml`

```toml
[project]
dependencies = [
    "django[argon2]>=6.1.3",
    "markdown-it-py>=3.0.0",
    "nh3>=0.2.18",
]

[project.optional-dependencies]
dev = [
    # easymde no es paquete Python — se descargan archivos JS/CSS a static/vendor/easymde/
]
```

> **Nota**: `easymde` 2.21.0 no es paquete Python — se descargan sus archivos JS/CSS a `static/vendor/easymde/` y se sirven como estáticos. Licencia MIT incluida.

---

## G. UX y Accesibilidad

### Arquitectura de información
- Navbar fija: Brand, nave principal (Mis tareas, Nueva tarea), Search, User menu
- Listado: Vertical, centrado, 1 acción primaria (Nueva tarea)
- Detalle: Sidebar navegación + Main contenido, resize handle
- Búsqueda: Dialog modal, focus trap, Escape cierra

### Responsive breakpoints
| Breakpoint | Sidebar | Navbar | Editor |
|---|---|---|---|
| Mobile (<640px) | Drawer off-canvas | Hamburger menu | Single column |
| Tablet (640-1024px) | 16rem fijo | Completa | Single column |
| Desktop (≥1024px) | 20rem resizable | Completa | Split view opcional |

### Accesibilidad (WCAG 2.1 AA)
- Contraste: Texto principal 15.3:1, secundario 7.8:1
- Focus visible: Ring 3px magenta-subtle en todos los interactivos
- Teclado: Tab order lógico, Escape cierra dialogs, arrows en listas
- ARIA: labels en iconos, `aria-expanded` en dropdowns, `role="dialog"`
- Reduced motion: `@media (prefers-reduced-motion)` desactiva transiciones
- Zoom: Reflow hasta 200% sin scroll horizontal

---

## H. Seguridad

### Permisos (backend)
- `TaskAccessMixin.get_queryset()` filtra `authors=request.user`
- `CreatorRequiredMixin.dispatch()` valida `task.created_by == request.user`
- Formularios validan `is_active` y existencia de usuarios

### CSRF
- Todos los formularios POST incluyen `{% csrf_token %}`
- Logout solo POST (405 en GET)

### Markdown / XSS
- **Almacenamiento**: Markdown original (TextField)
- **Parser**: `markdown-it-py` (CommonMark, extensible, MIT)
- **Sanitizador servidor**: `nh3` (Rust/PyO3, allowlist-based, rápido, mantenido)
- **Sanitizador cliente (opcional)**: `DOMPurify` solo para preview instantáneo — nunca sustituye sanitización servidor
- **Allowlist explícita**: h1-h6, p, ul/ol/li, strong/em, code/pre, blockquote, a[href], img[src/alt], table, hr, input[type=checkbox]
- **Bloqueado**: `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `javascript:`, `data:`, `vbscript:`, `onclick`, `onload`, `onerror`, `onmouseover`
- **Función centralizada**: `render_markdown_safe(markdown_text)` compartida por vista detallada y preview
- **Vista previa y detalle**: Mismas reglas de sanitización

### Rate limiting
- No implementado en Fase 2 (documentado como limitación pre-producción)
- ModelBackend no incluye rate limiting nativo
- **SECURITY-01**: Rate limiting obligatorio antes del despliegue público (registrado como requisito pendiente)

---

## I. Testing plan

| Categoría | Tests clave |
|---|---|
| **Modelo** | Creación, title requerido, body vacío, status choices, fechas auto, FK/M2M, protección created_by |
| **Creación** | Asignación creador, inclusión en authors, coautores válidos, rechazo inactivos/inexistentes, atomicidad |
| **Permisos** | Listado aislado, detalle 404 ajeno, edición solo authors, gestión solo creador, 3+ users con tareas compartidas |
| **Markdown** | Persistencia, saltos línea, headers, lists, code, sanitización XSS, protocolos peligrosos bloqueados |
| **Tests de sanitización (nuevos)** | XSS vectors: `<script>`, `<img onerror>`, `<svg onload>`, `javascript:` href; Protocolos: `javascript:`, `data:`, `vbscript:`; Atributos eventos: `onclick`, `onload`, `onerror`; Tags no permitidos: `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`; Allowlist positiva; Vista previa y detalle comparten `render_markdown_safe()` |
| **UI** | Login/Registro visual, listado, creación, detalle, editor, search, sidebar resize, responsive, feedback |
| **Integración** | Flujo completo: register → login → create → edit → search → logout |

**Comandos de verificación:**
```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py showmigrations
uv run python manage.py test tasksite.accounts tasksite.tasks
```

---

## J. Tasks y dependencias

| ID | Specs | Descripción | Dependencias | Commit |
|---|---|---|---|---|
| T1 | S11 | Design system: tokens, global CSS, components, layout | — | feat: design system foundation |
| T2 | S1 | Modelo Task + Manager + Apps | T1 | feat: tasks - Task model |
| T3 | S13 | Migraciones tasks (verificar en BD test) | T2 | feat: tasks - migrations |
| T4 | S2,S3 | Services: create_task, update_authors, transacciones | T2 | feat: tasks - services layer |
| T5 | S2,S3 | Forms: TaskForm, TaskEditForm, AuthorManagementForm | T2,T4 | feat: tasks - forms |
| T6 | S3 | Mixins permisos: TaskAccessMixin, CreatorRequiredMixin | T2 | feat: tasks - permissions |
| T7 | S4,S9 | Views: ListView, CreateView + URLs + config/urls | T2,T5,T6 | feat: tasks - list & create |
| T8 | S5 | Search: vista, dialog, JS, Q filtering | T7 | feat: tasks - search |
| T9 | S6,S8 | DetailView: layout 2 paneles, sidebar resize, metadatos | T7 | feat: tasks - detail view |
| T10 | S7 | Editor MD: toolbar, textarea, preview, sanitización | T1 | feat: tasks - markdown editor |
| T11 | S8 | Author management view + form + permisos | T5,T6 | feat: tasks - author management |
| T12 | S11 | Templates tasks + actualización visual accounts | T1,T7,T9 | feat: tasks - templates & auth redesign |
| T13 | S12 | Tests completos (modelo, creación, permisos, MD, UI) | T2-T11 | feat: tasks - tests |
| T14 | S9,S12 | Validación final: check, migraciones, tests, servidor | T13 | feat: tasks - final verification |

**Orden crítico:** T1 → T2 → T3 → (T4,T5,T6) → T7 → (T8,T9,T10,T11) → T12 → T13 → T14

---

## K. Riesgos y decisiones pendientes

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Editor Markdown** | Medio | **Decidido: EasyMDE 2.21.0** — toolbar funcional, sin build, MIT. Migración futura a CM6 si necesario |
| **Sanitización HTML** | Alto | **Decidido: markdown-it-py + nh3 (server) + DOMPurify opcional (client preview)** — allowlist, función centralizada |
| **Sidebar resize móvil** | Bajo | Drawer off-canvas como fallback; probar en dispositivos reales |
| **Búsqueda performance** | Bajo | Solo title+body en Fase 2; añadir índices SQLite si necesario |
| **Multi-select coautores** | Bajo | `<select multiple>` nativo + enhancement JS; fallback accesible |
| **Migraciones M2M** | Medio | Verificar tabla intermedia `task_authors` creada correctamente; probar en BD limpia |

### Decisiones finalizadas
1. **Editor**: **EasyMDE 2.21.0** — basado en CodeMirror 5, toolbar lista, sin build step, licencia MIT, archivos estáticos locales
2. **Sanitización**: **markdown-it-py** (parser) + **nh3** (sanitizador server, Rust/PyO3, allowlist) + **DOMPurify** opcional (client preview) — función centralizada `render_markdown_safe()`
3. **Íconos**: **SVG inline** — performance, control total, sin dependencias
4. **CSS Strategy**: **CSS Custom Properties nativas** — sin Node.js, sin PostCSS, sin build step
5. **Rate limiting**: **No en Fase 2** — documentado como `SECURITY-01` para pre-producción
6. **Inter font**: Google Fonts en prototipos; local en `static/fonts/` en producción

---

## L. Log de trabajo

| Entrada | Descripción |
|---|---|
| L1 | Request original Fase 2 recibido |
| L2 | Inspección repo Fase 1: accounts funcionando, auth Argon2id, login username/email |
| L3 | Skills leídas: gentle-ai-design (tokens, Tailwind v4), gentle-ui (UX, componentes) |
| L4 | Auditoría visual: base.html/login/register/dashboard usan CSS light custom → requieren migración a dark-first Gentle-AI |
| L5 | Documento feature creado: `odd/tasks/tasks-core.md` con Specs S1-S13 y Tasks T1-T14 |
| L6 | Design system documentado: `design/system.md` |
| L7 | CSS global creado: design-tokens.css, global.css, components.css, layout.css, markdown.css |
| L8 | Prototipos HTML: login, register, task-list, task-detail, markdown-editor |
| L9 | Planificación consolidada en `PLANIFICACION_FASE2.md` |
| L10 | Auditoría contraste WCAG 2.1 AA completada — `--color-text-tertiary` corregido `#52525b`→`#a1a1aa`, badges con texto oscuro |
| L11 | Decisiones técnicas finalizadas: EasyMDE 2.21.0, markdown-it-py + nh3, DOMPurify opcional, CSS nativo |
| L12 | Tests de sanitización Markdown añadidos (XSS vectors, protocolos peligrosos, allowlist) |
| L13 | Documentación actualizada: design/system.md, PLANIFICACION_FASE2.md, odd/tasks/tasks-core.md |
| L14 | T1 Foundation: CSS completado, pendiente integración templates Django |

---

## Próximos pasos

1. ✅ **Planificación y diseño completados** (este documento + prototipos)
2. ⏳ **Revisión técnica y visual** por el usuario
3. ⏳ **Aprobación** para comenzar implementación
4. ⏳ **Implementación T1-T14** en orden de dependencias
5. ⏳ **Validación final** con comandos de verificación

---

**Estado**: Listo para revisión y aprobación.  
**Entregables**: `odd/tasks/tasks-core.md`, `design/system.md`, 5 archivos CSS, 5 prototipos HTML, `PLANIFICACION_FASE2.md`.