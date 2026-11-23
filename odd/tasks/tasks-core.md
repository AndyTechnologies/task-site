# Fase 2 — Tasks Core + Gentle-AI Design System

## Specs

### S1: Modelo Task
Crear modelo `Task` en `tasksite.tasks.models` con campos:
- `id`: BigAutoField (PK)
- `title`: CharField, obligatorio, max 200 caracteres
- `body`: TextField, Markdown, opcional
- `status`: CharField con TextChoices (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)
- `created_by`: ForeignKey a `settings.AUTH_USER_MODEL`, `on_delete=PROTECT`, obligatorio
- `authors`: ManyToManyField a `settings.AUTH_USER_MODEL`, related_name descriptivo
- `created_at`: DateTimeField auto_now_add
- `updated_at`: DateTimeField auto_now

El creador se incluye automáticamente en `authors` al crear la tarea. El creador no puede eliminarse de `authors`.

### S2: Creación de tareas
Formulario con: título, body Markdown opcional, coautores adicionales.
- Usuario autenticado = creador obligatorio
- Transacción atómica: crea tarea + asigna created_by + añade creador a authors + añade coautores
- Redirige a detalle tras creación
- Solo usuarios activos y existentes como coautores

### S3: Permisos y aislamiento multiusuario
Un usuario solo accede a tareas donde esté en `authors`.
Aplicable a: listado, búsqueda, detalle, edición, sidebar, gestión de autores.
QuerySets filtrados en backend. Acceso a tareas ajenas → 404.

**Permisos de operación:**
- Todos los authors: consultar, editar body, modificar estado
- Solo creador: añadir/retirar coautores
- Nunca eliminar al creador de authors
- Nunca sustituir el creador original

### S4: Vista principal (ListView)
Reemplaza dashboard de Fase 1. `LoginRequiredMixin` + `ListView`.
- Tareas accesibles al usuario autenticado
- Listado vertical, centrado horizontalmente
- Título principal, estado visible, elementos seleccionables
- Navegación a detalle, acción crear tarea
- Estado vacío: explicación + acción crear primera tarea

### S5: Búsqueda
Diálogo `<dialog>` con JavaScript nativo.
- Abrir/cerrar, escribir búsqueda, buscar por título y body
- Cancelar, cerrar con Escape, navegación teclado
- GET en servidor, `Q` para combinar condiciones
- QuerySet filtrado por tareas accesibles
- Sin resultados: mantener término, explicar, permitir limpiar

### S6: Vista detallada (DetailView)
Layout de dos paneles:
1. **Barra lateral izquierda**: lista tareas accesibles, título + estado selección, truncado con ellipsis, navegación entre tareas
2. **Área principal**: contenido y edición

**Redimensionamiento sidebar:**
- Anchura inicial, mínima, máxima
- Redimensionamiento horizontal
- Contenido adaptable, accesibilidad teclado, foco visible
- Adaptación móvil: navegación colapsable
- Sin dependencias externas

### S7: Editor Markdown
**Decisión: EasyMDE 2.21.0** (basado en CodeMirror 5).

Justificación: Toolbar funcional, ligero, sin build step, licencia MIT, compatible con textarea nativo, reduce complejidad vs CodeMirror 6.

Requisitos:
- Archivos estáticos locales en `static/vendor/easymde/` (no CDN)
- No cadena de construcción frontend
- Conservar licencia MIT en `static/vendor/easymde/LICENSE`
- Documentar actualización: descargar release GitHub, reemplazar archivos
- Compatibilidad Gentle-AI: toolbar personalizable, themes CSS variables
- Vista previa: nunca insertar HTML no sanitizado (usa nh3 server-side + DOMPurify client-side opcional)

Soportar: encabezados, negrita, cursiva, listas, enlaces, código, saltos de línea, guardado, feedback, vista previa.

**Seguridad:**
- Conservar Markdown original en SQLite (TextField)
- Renderizado seguro: parser `markdown-it-py` + sanitizador `nh3` (allowlist)
- Deshabilitar HTML arbitrario en Markdown (`html: false`)
- Allowlist explícita: h1-h6, p, ul/ol/li, strong/em, code/pre, blockquote, a[href], img[src/alt], table, hr, input[type=checkbox]
- Bloquear `javascript:`, `data:`, `vbscript:`, `onclick`, `onerror`, etc.
- No usar `safe`/`mark_safe` sin sanitización
- Políticas idénticas en vista detallada y vista previa

### S8: Información y metadatos
En vista detallada: título, estado, creador, fecha creación, última modificación, autores, coautores.
- Autores editan body y estado
- Solo creador gestiona colaboradores
- Título sin edición en esta fase

### S9: URLs y navegación
Namespace `tasks`:
```
/tasks/           Listado (reemplaza dashboard)
/tasks/new/       Creación
/tasks/<pk>/      Detalle
/tasks/<pk>/edit/ Edición
/tasks/<pk>/authors/ Gestión de autores
```
Integrar en `config/urls.py`. Actualizar `LOGIN_REDIRECT_URL` a `tasks:list`. Conservar compatibilidad con accounts.

### S10: Arquitectura POO
- Modelos, Model Managers, ModelForms
- ListView, CreateView, DetailView, UpdateView
- LoginRequiredMixin
- Herencia, sobrescritura, encapsulación
- Transacciones atómicas
- `services.py` para: creación tareas, asignación autores, modificación colaboradores
- Sin CQRS, Unit of Work, repositorios artificiales

### S11: Sistema visual Gentle-AI (compartido accounts + tasks)
Basado en skills `gentle-ai-design` y `gentle-ui`.

**Tokens (CSS custom properties) — auditados WCAG 2.1 AA:**
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

**Tipografía:** Inter (UI), ui-monospace (código). Pesos: 400/500/600/700/800.
> Fuente Inter: Google Fonts en prototipos; local en `static/fonts/` en producción.

**Estructura:** Contenedor max-w-6xl, nav fija con backdrop-blur, rounded-lg (8px), rounded-2xl (16px), spacing 4px grid.

**Componentes compartidos:** Layout, navegación, botones, campos, formularios, mensajes, badges estado, listas, diálogos, sidebar, resize handle, toolbar Markdown, editor, preview.

**Login/Registro:** Actualización visual a Gentle-AI, mismo comportamiento, componentes compartidos.

**Responsive/Accesibilidad:** Desktop/tablet/móvil, teclado, contraste, focus visible, reduced motion, nombres accesibles, enlaces para navegar/botones para acciones.

**Estrategia CSS:** CSS Custom Properties nativas (no Tailwind v4 build) — sin Node.js, sin PostCSS.

### S12: Testing
**Modelo:** creación, título obligatorio, body vacío, estados, fechas, relaciones creador/autores, M2M, protección creador histórico.

**Creación:** asignación automática creador, inclusión en authors, coautores, rechazo inactivos/inexistentes, atomicidad.

**Permisos:** aislamiento listado/detalle/edición/búsqueda, permisos authors, gestión exclusiva creador. Mínimo 3 usuarios y tareas compartidas.

**Markdown:** persistencia, saltos línea, encabezados, listas, código, sanitización, bloqueo XSS, bloqueo protocolos peligrosos.

**Tests de sanitización (nuevos):**
- XSS vectors: `<script>`, `<img onerror>`, `<svg onload>`, `javascript:` href
- Protocolos peligrosos: `javascript:`, `data:`, `vbscript:` en links/imágenes
- Atributos de eventos: `onclick`, `onload`, `onerror`, `onmouseover`
- HTML tags no permitidos: `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`
- Allowlist positiva: solo tags/attrs definidos explícitamente
- Vista previa y detalle comparten misma función `render_markdown_safe()`

**Interfaz:** login, registro, listado, creación, detalle, editor, búsqueda, navegación, sidebar, responsive, feedback.

### S13: Migraciones
Generar migraciones aditivas para `tasks`. No modificar `accounts`. No reconstruir SQLite. Usar `settings.AUTH_USER_MODEL`. Verificar dependencias, FK, M2M, tabla intermedia, integridad. Probar en SQLite independiente antes de desarrollo.

---

## Tasks

| ID | Specs | Route | Commit |
|---|---|---|---|
| T1 | S10, S11 | Inspección e integración: leer skills, auditar UI existente, definir design system tokens, crear CSS base compartido | feat: tasks - design system foundation |
| T2 | S1 | Modelo Task: models.py, apps.py, managers.py | feat: tasks - Task model |
| T3 | S13 | Migraciones: makemigrations tasks, verificar, aplicar en BD test | feat: tasks - migrations |
| T4 | S2, S3 | Servicios: services.py (creación, autores, colaboradores), transacciones, validaciones | feat: tasks - services layer |
| T5 | S2, S3 | Formularios: forms.py (TaskForm, TaskEditForm, AuthorManagementForm) | feat: tasks - forms |
| T6 | S3 | Permisos: mixins, queryset filtering, decoradores | feat: tasks - permissions |
| T7 | S4, S9 | Vistas base: ListView (list), CreateView (new), URLs tasks, integrar en config/urls | feat: tasks - list & create views |
| T8 | S5 | Búsqueda: vista, formulario, diálogo <dialog>, JS nativo | feat: tasks - search |
| T9 | S6, S8 | Detalle: DetailView, layout dos paneles, sidebar redimensionable, metadatos | feat: tasks - detail view |
| T10 | S7 | Editor Markdown: evaluación, integración, toolbar, preview, sanitización | feat: tasks - markdown editor |
| T11 | S8 | Gestión autores: vista, formulario, permisos creador | feat: tasks - author management |
| T12 | S11 | Sistema visual compartido: CSS base, componentes, actualización login/registro | feat: tasks - shared design system |
| T13 | S11 | Templates tasks: list.html, detail.html, form.html, partials | feat: tasks - templates |
| T14 | S12 | Testing completo: modelo, creación, permisos, markdown, interfaz | feat: tasks - tests |
| T15 | S9, S12 | Validación final: check, migraciones, tests, servidor, funcionalidad, responsive | feat: tasks - final verification |

---

## Log

L1: Inicio planificación Fase 2 — Tasks Core + Gentle-AI Design System (request original verbatim)
L2: Inspección repo Fase 1 completada: accounts funcionando, auth con Argon2id, login username/email
L3: Skills leídas: gentle-ai-design (tokens, Tailwind v4 @theme), gentle-ui (principios UX, componentes)
L4: Auditoría visual completada: base.html/login/register/dashboard usan CSS light custom, requieren migración a dark-first Gentle-AI
L5: Documento de feature creado con Specs S1-S13 y Tasks T1-T15
L6: CSS Design System creado (5 archivos): design-tokens.css, global.css, components.css, layout.css, markdown.css
L7: 5 prototipos HTML: login, register, task-list, task-detail, markdown-editor
L8: Auditoría contraste WCAG 2.1 AA completada — `--color-text-tertiary` corregido `#52525b`→`#a1a1aa`, badges con texto oscuro
L9: Decisiones técnicas finalizadas: EasyMDE 2.21.0, markdown-it-py + nh3, DOMPurify opcional, CSS nativo
L10: Tests de sanitización Markdown añadidos (XSS vectors, protocolos peligrosos, allowlist)
L11: Documentación actualizada: design/system.md, PLANIFICACION_FASE2.md, odd/tasks/tasks-core.md
L12: T1 Foundation: CSS completado, pendiente integración templates Django