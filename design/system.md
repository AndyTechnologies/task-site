# TaskSite — Gentle-AI Design System

> Documento generado tras leer `gentle-ai-design/SKILL.md` y `gentle-ui/SKILL.md` locales.
> Define la identidad visual, tokens, componentes y reglas para toda la aplicación (accounts + tasks).

---

## 1. Identidad visual

### 1.1 Dirección

**Dark-first**, zinc background, acento magenta único. Experiencia profesional, minimalista, consistente.

| Concepto | Valor |
|---|---|
| Background principal | `#09090b` (zinc-950) |
| Superficie tarjetas | `#111113` (zinc-900) |
| Superficie código/editor | `#18181c` (zinc-900 más oscuro) |
| Acento principal | `#ea1889` (magenta-600) |
| Acento hover | `#ff6db0` (magenta-400) |
| Acento sutil | `#ea188926` (10% opacity) |
| Texto principal | `#fafafa` (zinc-50) |
| Texto secundario | `#a1a1aa` (zinc-400) |
| Texto terciario | `#a1a1aa` (zinc-400) — **corregido de #52525b para WCAG AA** |
| Bordes | `#ffffff12` (7% white) |
| Bordes hover/focus | `#ea188959` (35% magenta) |

### 1.2 Estados semánticos (derivados)

| Estado | Color | Uso |
|---|---|---|
| Error | `#f43f5e` (rose-500) | Errores validación, acciones destructivas |
| Warning | `#fbbf24` (amber-400) | Advertencias, estados pendientes |
| Success | `#34d399` (emerald-400) | Éxito, completado |
| Info | `#ea1889` (magenta-600) | Información, enlaces, acento |

### 1.3 Tipografía

| Rol | Fuente | Pesos |
|---|---|---|
| UI (títulos, cuerpo, UI) | `Inter, system-ui, -apple-system, sans-serif` | 400, 500, 600, 700, 800 |
| Código (editor, preview, mono) | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` | 400, 500 |

**Escala tipográfica (rem):**
- Display: 2.25rem / 700
- H1: 1.875rem / 700
- H2: 1.5rem / 600
- H3: 1.25rem / 600
- Body: 1rem / 400
- Body-sm: 0.875rem / 400
- Caption: 0.75rem / 500
- Code: 0.875rem / 400 (mono)

> **Fuente Inter**: Se carga vía Google Fonts en prototipos; en producción se descargará localmente a `static/fonts/` para privacidad y rendimiento.

### 1.4 Espaciado y estructura

- Grid base: 4px (0.25rem)
- Contenedor principal: `max-width: 72rem` (1152px) centrado
- Padding contenedor: `1rem` móvil, `1.5rem` tablet, `2rem` desktop
- Gap entre elementos: `1rem` (16px) base

### 1.5 Radios

| Elemento | Radio | Valor |
|---|---|---|
| Controles (inputs, botones, badges) | `rounded-lg` | 8px |
| Tarjetas, paneles, diálogos | `rounded-2xl` | 16px |
| Elementes pequeños (avatars, chips) | `rounded-full` | 9999px |

### 1.6 Sombras y elevación

- **Nivel 0 (base)**: Sin sombra, borde `#ffffff12`
- **Nivel 1 (hover)**: `box-shadow: 0 0 0 1px #ea188959`
- **Nivel 2 (elevado/dropdown/dialog)**: `box-shadow: 0 10px 40px -10px #00000080, 0 0 0 1px #ffffff12`
- **Nivel 3 (modal)**: Nivel 2 + overlay backdrop

### 1.7 Transiciones

- Duración: 150ms
- Easing: `ease-out`
- Propiedades: `color, background-color, border-color, box-shadow, opacity`

---

## 2. Componentes base

### 2.1 Botones

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1.25;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 150ms ease-out;
  text-decoration: none;
  white-space: nowrap;
}

.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-accent-subtle), 0 0 0 1px var(--color-accent);
}

/* Variantes */
.btn-primary {
  background: var(--color-accent);
  color: #09090b;
  border-color: var(--color-accent);
}
.btn-primary:hover { background: var(--color-accent-hover); }
.btn-primary:active { background: #c01470; }

.btn-secondary {
  background: transparent;
  color: var(--color-text);
  border-color: var(--color-border);
}
.btn-secondary:hover { background: var(--color-bg-card); border-color: var(--color-border-hover); }

.btn-ghost {
  background: transparent;
  color: var(--color-text-muted);
  border-color: transparent;
}
.btn-ghost:hover { background: var(--color-bg-card); color: var(--color-text); }

.btn-danger {
  background: transparent;
  color: var(--color-error);
  border-color: var(--color-error);
}
.btn-danger:hover { background: #f43f5e1a; }

/* Tamaños */
.btn-sm { padding: 0.375rem 0.75rem; font-size: 0.8125rem; }
.btn-lg { padding: 0.875rem 1.5rem; font-size: 1rem; }

/* Estados */
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-loading { position: relative; color: transparent; }
.btn-loading::after {
  content: "";
  position: absolute;
  width: 1rem; height: 1rem;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

### 2.2 Campos de formulario

```css
.form-field { display: flex; flex-direction: column; gap: 0.375rem; }

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.625rem 0.875rem;
  font-size: 0.875rem;
  font-family: inherit;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: border-color 150ms, box-shadow 150ms;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-subtle);
}

.form-input::placeholder,
.form-textarea::placeholder { color: var(--color-text-tertiary); }

.form-input:disabled,
.form-textarea:disabled,
.form-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-help { font-size: 0.75rem; color: var(--color-text-tertiary); }
.form-error { font-size: 0.75rem; color: var(--color-error); }

/* Error state */
.form-field.has-error .form-input,
.form-field.has-error .form-textarea,
.form-field.has-error .form-select {
  border-color: var(--color-error);
}
.form-field.has-error .form-input:focus,
.form-field.has-error .form-textarea:focus,
.form-field.has-error .form-select:focus {
  box-shadow: 0 0 0 3px #f43f5e26;
}
```

### 2.3 Tarjetas (Cards)

```css
.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.5rem;
}

.card-hover {
  transition: border-color 150ms, box-shadow 150ms;
}
.card-hover:hover {
  border-color: var(--color-border-hover);
  box-shadow: 0 4px 24px -4px #00000060;
}
```

### 2.4 Badges de estado

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
  white-space: nowrap;
}

/* Badges con fondo de estado — texto oscuro para contraste WCAG AA */
.badge-pending { background: var(--color-warning); color: #09090b; }
.badge-in_progress { background: var(--color-info); color: #09090b; }
.badge-completed { background: var(--color-success); color: #09090b; }
.badge-cancelled { background: var(--color-text-tertiary); color: #09090b; }

/* Variante outline para menos peso visual */
.badge-outline {
  background: transparent;
  border: 1px solid currentColor;
}
```

### 2.5 Navegación principal

```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: #000000cc;
  backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--color-border);
}

.navbar-inner {
  max-width: 72rem;
  margin: 0 auto;
  padding: 0 1rem;
  height: 3.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.navbar-brand {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
  letter-spacing: -0.02em;
}
.navbar-brand:hover { color: var(--color-accent); }

.navbar-nav { display: flex; align-items: center; gap: 0.5rem; }
.navbar-link {
  padding: 0.5rem 0.875rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-muted);
  border-radius: 8px;
  text-decoration: none;
  transition: color 150ms, background 150ms;
}
.navbar-link:hover { color: var(--color-text); background: var(--color-bg-card); }
.navbar-link.active { color: var(--color-accent); background: var(--color-accent-subtle); }
```

### 2.6 Diálogos (Dialog)

```css
dialog {
  border: none;
  border-radius: 16px;
  padding: 0;
  background: var(--color-bg-card);
  box-shadow: 0 20px 60px -10px #00000080, 0 0 0 1px var(--color-border);
  max-width: 32rem;
  width: 90vw;
  max-height: 85vh;
  overflow: hidden;
}

dialog::backdrop {
  background: #00000080;
  backdrop-filter: blur(4px);
  animation: fade-in 150ms ease-out;
}

@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.dialog-title { font-size: 1.125rem; font-weight: 600; color: var(--color-text); }

.dialog-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem; height: 2rem;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.dialog-close:hover { color: var(--color-text); background: var(--color-bg-code); }

.dialog-content { padding: 1.5rem; overflow-y: auto; }

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
}
```

### 2.7 Lista de tareas (ListView item)

```css
.task-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: border-color 150ms, box-shadow 150ms, background 150ms;
}
.task-item:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-code);
  box-shadow: 0 4px 24px -4px #00000040;
}
.task-item:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-subtle);
}

.task-item-main { flex: 1; min-width: 0; }
.task-item-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}
.task-item-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}
```

### 2.8 Sidebar redimensionable

```css
.layout {
  display: grid;
  grid-template-columns: 20rem 1fr;
  min-height: calc(100vh - 3.5rem);
}

.sidebar {
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 14rem;
  max-width: 32rem;
}

.sidebar-header {
  padding: 1rem 1rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-tertiary);
}

.sidebar-list { flex: 1; overflow-y: auto; padding: 0.5rem; }

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sidebar-item:hover { background: var(--color-bg-code); color: var(--color-text); }
.sidebar-item.active { background: var(--color-accent-subtle); color: var(--color-accent); }
.sidebar-item.active .task-item-title { color: var(--color-accent); }

.resize-handle {
  position: absolute;
  top: 0; right: 0;
  width: 4px;
  height: 100%;
  cursor: col-resize;
  background: transparent;
  transition: background 150ms;
}
.resize-handle:hover,
.resize-handle.dragging { background: var(--color-accent); }
.resize-handle::after {
  content: "";
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 2px; height: 1.5rem;
  background: var(--color-border);
  border-radius: 1px;
  opacity: 0;
  transition: opacity 150ms;
}
.resize-handle:hover::after { opacity: 1; }
```

### 2.9 Editor Markdown

```css
.markdown-editor {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-code);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden.
}

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
}

.editor-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem; height: 2rem;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: color 150ms, background 150ms;
}
.editor-btn:hover { color: var(--color-text); background: var(--color-bg); }
.editor-btn.active { color: var(--color-accent); background: var(--color-accent-subtle); }

.editor-btn:focus-visible { outline: none; box-shadow: 0 0 0 2px var(--color-accent); }

.editor-textarea {
  flex: 1;
  min-height: 24rem;
  padding: 1rem;
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--color-text);
  background: transparent;
  border: none;
  resize: vertical;
  outline: none.
}
.editor-textarea::placeholder { color: var(--color-text-tertiary); }

/* Preview */
.markdown-preview {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow-x: auto.
}

.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3 { color: var(--color-text); margin-top: 1.5em; margin-bottom: 0.5em; }
.markdown-preview h1 { font-size: 1.5rem; border-bottom: 1px solid var(--color-border); padding-bottom: 0.5rem; }
.markdown-preview h2 { font-size: 1.25rem; }
.markdown-preview h3 { font-size: 1rem; }

.markdown-preview p { margin: 1em 0; line-height: 1.7; }
.markdown-preview ul, .markdown-preview ol { margin: 1em 0; padding-left: 1.5rem; }
.markdown-preview li { margin: 0.5em 0; }
.markdown-preview code { font-family: var(--font-mono); font-size: 0.875rem; background: var(--color-bg-code); padding: 0.125rem 0.375rem; border-radius: 4px; }
.markdown-preview pre { background: var(--color-bg-code); border: 1px solid var(--color-border); border-radius: 8px; padding: 1rem; overflow-x: auto; margin: 1em 0; }
.markdown-preview pre code { background: transparent; padding: 0; font-size: 0.8125rem; line-height: 1.6; }
.markdown-preview a { color: var(--color-accent); text-decoration: underline; text-underline-offset: 2px; }
.markdown-preview blockquote { border-left: 3px solid var(--color-accent); padding-left: 1rem; color: var(--color-text-muted); margin: 1em 0; }
.markdown-preview hr { border: none; border-top: 1px solid var(--color-border); margin: 2em 0; }
```

### 2.10 Estados vacíos

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--color-text-muted);
}

.empty-state-icon {
  width: 4rem; height: 4rem;
  color: var(--color-text-tertiary);
  margin-bottom: 1rem;
}

.empty-state-title { font-size: 1.125rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.5rem; }
.empty-state-description { font-size: 0.875rem; max-width: 20rem; margin-bottom: 1.5rem; }
```

---

## 3. Pantallas diseñadas

### 3.1 Login (`/cuentas/login/`)

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: TaskSite (brand)                    [Login] [Reg]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────────────┐                  │
│                    │      TaskSite       │                  │
│                    │  Iniciar sesión     │                  │
│                    │                     │                  │
│                    │  ┌───────────────┐  │                  │
│                    │  │ Usuario o     │  │  ← Form-input    │
│                    │  │ correo@ejemplo│  │                  │
│                    │  └───────────────┘  │                  │
│                    │                     │                  │
│                    │  ┌───────────────┐  │                  │
│                    │  │ Contraseña    │  │  ← Form-input    │
│                    │  │ ••••••••••••  │  │                  │
│                    │  └───────────────┘  │                  │
│                    │                     │                  │
│                    │  [ Iniciar sesión ] │  ← btn-primary   │
│                    │                     │                  │
│                    │  ¿No tienes cuenta? │                  │
│                    │  [Registrarse]      │  ← btn-ghost     │
│                    └─────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Card centrada, max-width 28rem
- Fondo `#09090b`, card `#111113`
- Inputs con focus ring magenta
- Botón primario magenta, ghost para registro

### 3.2 Registro (`/cuentas/registro/`)

Igual que login con 4 campos: username, email, password, confirmar password.

### 3.3 Listado principal (`/tasks/`)

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: TaskSite    [Buscar]    [Usuario ▼] [Nueva tarea]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Mis tareas                                    [+]  │   │
│   │                                                     │   │
│   │  ┌─────────────────────────────────────────────┐   │   │
│   │  │ Configurar CI/CD          ● En proceso     │   │   │
│   │  │ Pipeline GitHub Actions para deploy...      │   │   │
│   │  └─────────────────────────────────────────────┘   │   │
│   │                                                     │   │
│   │  ┌─────────────────────────────────────────────┐   │   │
│   │  │ Documentación API           ○ Pendiente    │   │   │
│   │  │ Escribir docs OpenAPI para endpoints...     │   │   │
│   │  └─────────────────────────────────────────────┘   │   │
│   │                                                     │   │
│   │  ┌─────────────────────────────────────────────┘   │   │
│   │  │ Refactor auth module        ✓ Realizada    │   │   │
│   │  │ Migrado a custom user model + Argon2id      │   │   │
│   │  └─────────────────────────────────────────────┘   │   │
│   │                                                     │   │
│   │  (estado vacío si no hay tareas)                   │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Botón "Nueva tarea" (btn-primary) fixed bottom-right o en header
- Búsqueda en header abre diálogo
- Lista vertical, cards con hover, click → detalle

### 3.4 Diálogo de búsqueda

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar...                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────────────┐  ← dialog        │
│                    │  Buscar tareas      │                  │
│                    │  ─────────────────  │                  │
│                    │                     │                  │
│                    │  ┌───────────────┐  │                  │
│                    │  │ Buscar título │  │  ← input + icon  │
│                    │  │ y contenido...│  │                  │
│                    │  └───────────────┘  │                  │
│                    │                     │                  │
│                    │  Busca en títulos y │                  │
│                    │  contenido Markdown │                  │
│                    │                     │                  │
│                    │  [Cancelar] [Buscar]│                  │
│                    └─────────────────────┘                  │
│                                                             │
│    (backdrop blur oscurece fondo)                          │
└─────────────────────────────────────────────────────────────┘
```

- `<dialog>` nativo, abre con `[Buscar]` en navbar
- Escape cierra, focus trap
- GET a `/tasks/?q=...`

### 3.5 Creación de tarea (`/tasks/new/`)

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: TaskSite ← Volver    [Guardar borrador] [Crear]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Nueva tarea                                        │   │
│   │                                                     │   │
│   │  ┌─────────────────────────────────────────────┐   │   │
│   │   Título *                                     │   │
│   │   ┌─────────────────────────────────────────┐  │   │
│   │   │ Mi nueva tarea...                       │  │   │
│   │   └─────────────────────────────────────────┘  │   │
│   │                                                     │   │
│   │   Body (Markdown)                                 │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │ # Encabezado                              │   │   │
│   │   │                                           │   │   │
│   │   │ Texto en **negrita**, *cursiva*, `código` │   │   │
│   │   │                                           │   │   │
│   │   │ - Lista                                   │   │   │
│   │   │ - Items                                   │   │   │
│   │   │                                           │   │   │
│   │   │ ```python                                 │   │   │
│   │   │   print("hola")                           │   │   │
│   │   │ ```                                       │   │   │
│   │   └─────────────────────────────────────────┘   │   │
│   │   [Toolbar: H1 H2 B I ` ` Link List Code]       │   │
│   │                                                     │   │
│   │   Coautores (opcional)                            │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │ ▼ Seleccionar usuarios...               │   │   │  ← multi-select
│   │   └─────────────────────────────────────────┘   │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Layout centrado, max-width 48rem
- Editor Markdown full-width con toolbar
- Multi-select para coautores (solo usuarios activos)

### 3.6 Vista detallada (`/tasks/<pk>/`)

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: TaskSite ← Volver    [Buscar]  [Usuario ▼] [Editar]│
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│   SIDEBAR        │  MAIN CONTENT                            │
│   ─────────      │  ───────────                             │
│                  │                                          │
│   Mis tareas     │  ┌──────────────────────────────────┐   │
│   ────────────   │  │ Configurar CI/CD          ● En   │   │
│   ▸ Configurar   │  │                     proceso      │   │
│     CI/CD        │  ├──────────────────────────────────┤   │
│   ▸ Documentación│  │ # Configurar CI/CD               │   │
│     API          │  │                                  │   │
│   ▸ Refactor     │  │ Pipeline GitHub Actions para     │   │
│     auth         │  │ deploy automático...             │   │
│   ▸ Nueva tarea  │  │                                  │   │
│                  │  │ ## Pasos                         │   │
│   (scroll,       │  │                                  │   │
│    resize handle)│  │ - [ ] Configurar workflow        │   │
│                  │  │ - [ ] Tests                      │   │
│                  │  │ - [ ] Deploy staging             │   │
│                  │  │                                  │   │
│                  │  │ ```yaml                          │   │
│                  │  │ name: CI                         │   │
│                  │  │ ...                              │   │
│                  │  │ ```                              │   │
│                  │  ├──────────────────────────────────┤   │
│                  │  │ Meta:                            │   │
│                  │  │ Creado por: andy · hace 2 días   │   │
│                  │  │ Actualizado: hace 3 horas        │   │
│                  │  │ Autores: andy, maria             │   │
│                  │  └──────────────────────────────────┘   │
│                  │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

- Grid: sidebar 20rem (resizable 14-32rem), main 1fr
- Sidebar: lista tareas accesibles, item activo destacado
- Main: título + badge estado, body renderizado, metadatos
- Resize handle entre paneles
- Móvil: sidebar colapsable (drawer), botón hamburguesa

### 3.7 Editor Markdown (en detalle/creación)

Toolbar: H1, H2, **Bold**, *Italic*, `Code`, 🔗 Link, • List, 1. Ordered, ``` Code block, 👁 Preview toggle

Modo edición: textarea monoespaciada, syntax highlighting básico (opcional)
Modo preview: renderizado seguro (DOMPurify o similar), mismo estilo que detalle

### 3.8 Estados vacíos

**Sin tareas (listado):**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                        📋                                   │
│                  No hay tareas aún                          │
│                                                             │
│         Crea tu primera tarea para comenzar                 │
│                                                             │
│                    [ Crear tarea ]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sin resultados (búsqueda):**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                        🔍                                   │
│              No hay coincidencias para "deploy"             │
│                                                             │
│         Intenta con otros términos o limpia la búsqueda     │
│                                                             │
│                    [ Limpiar búsqueda ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Responsive breakpoints

| Breakpoint | Ancho | Cambios |
|---|---|---|
| Mobile | < 640px | Sidebar → drawer, navbar compacta, cards apiladas, toolbar editor scrollable |
| Tablet | 640-1024px | Sidebar 16rem, padding ajustado |
| Desktop | ≥ 1024px | Sidebar 20rem, layout completo |

---

## 5. Accesibilidad

### 5.1 Auditoría de contraste (WCAG 2.1 AA)

| Combinación | Ratio | AA Normal | AA Large | AAA Normal | Estado |
|---|---|---|---|---|---|
| Texto principal (`#fafafa`) on Background (`#09090b`) | 19.06:1 | ✅ | ✅ | ✅ | Pass |
| Texto principal on Card (`#111113`) | 18.07:1 | ✅ | ✅ | ✅ | Pass |
| Texto muted (`#a1a1aa`) on Background | 7.76:1 | ✅ | ✅ | ✅ | Pass |
| Texto muted on Card | 7.36:1 | ✅ | ✅ | ✅ | Pass |
| **Texto tertiary (`#a1a1aa`) on Background** | **7.76:1** | ✅ | ✅ | ✅ | **Corregido** |
| Acento (`#ea1889`) on Background | 4.73:1 | ✅ | ✅ | ❌ | Pass (AA) |
| Acento on Card | 4.48:1 | ❌ | ✅ | ❌ | Large only |
| **Texto inverse (`#09090b`) on Acento** | **4.73:1** | ✅ | ✅ | ❌ | **Pass** |
| Texto inverse on Warning (`#fbbf24`) | 11.92:1 | ✅ | ✅ | ✅ | Pass |
| Texto inverse on Success (`#34d399`) | 10.35:1 | ✅ | ✅ | ✅ | Pass |
| Texto inverse on Error (`#f43f5e`) | 5.42:1 | ✅ | ✅ | ❌ | Pass |
| Texto inverse on Info (`#ea1889`) | 4.73:1 | ✅ | ✅ | ❌ | Pass |

**Cambios aplicados tras auditoría:**
- `--color-text-tertiary`: `#52525b` → `#a1a1aa` (zinc-400) — era 2.57:1, ahora 7.76:1
- Badges de estado: texto oscuro (`#09090b`) sobre fondos de estado — todos ≥ 4.5:1
- `.btn-primary`: usa `var(--color-text-inverse)` = `#09090b` sobre acento — 4.73:1
- `--color-accent` en card (4.48:1) — solo para elementos large (títulos, badges)

### 5.2 Otros criterios

- **Focus visible**: Ring 3px magenta-subtle en todos los interactivos
- **Teclado**: Tab order lógico, Escape cierra diálogos, arrows en listas
- **ARIA**: `aria-label` en iconos, `aria-expanded` en dropdowns, `role="dialog"` en modales
- **Reduced motion**: `@media (prefers-reduced-motion: reduce)` desactiva transiciones
- **Zoom**: Layout reflow hasta 200% sin scroll horizontal

---

## 6. Implementación CSS

### 6.1 Estrategia: CSS Custom Properties (no Tailwind v4 build)

**Razón**: Proyecto Django simple, sin Node.js, sin proceso de build frontend. Tailwind v4 requiere PostCSS + build step. CSS custom properties nativas dan misma funcionalidad de tokens sin dependencias.

### 6.2 Archivos

```
src/tasksite/
├── static/
│   └── css/
│       ├── design-tokens.css      # :root { --color-*: ... }
│       ├── components.css         # .btn, .form-input, .card, etc.
│       ├── layout.css             # .navbar, .layout, .sidebar, .dialog
│       ├── markdown.css           # .markdown-editor, .markdown-preview
│       └── global.css             # reset, base, utilities
└── tasksite/
    ├── accounts/
    │   └── templates/accounts/base.html  # carga global.css + components.css
    └── tasks/
        └── templates/tasks/base.html     # hereda o incluye lo mismo
```

### 6.3 Carga en templates

```html
<!-- base.html compartido -->
<link rel="stylesheet" href="{% static 'css/global.css' %}">
<link rel="stylesheet" href="{% static 'css/components.css' %}">
<link rel="stylesheet" href="{% static 'css/layout.css' %}">
{% block extra_css %}{% endblock %}
```

En `tasks/base.html`:
```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/markdown.css' %}">
{% endblock %}
```

---

## 7. Decisiones técnicas finalizadas

| Tema | Decisión | Justificación |
|---|---|---|
| **Editor Markdown** | **EasyMDE 2.21.0** (basado en CodeMirror 5) | Toolbar funcional, ligero, sin build step, licencia MIT, compatible con textarea nativo |
| **Parser Markdown** | **markdown-it-py** | Activamente mantenido, CommonMark compliant, extensible, licencia MIT |
| **Sanitizador HTML** | **nh3** (Rust, vía PyO3) | Rápido, seguro, allowlist-based, activamente mantenido (vs bleach sin mantenimiento) |
| **Sanitización cliente** | **DOMPurify** (opcional, solo preview) | Defensa en profundidad para preview instantáneo; nunca sustituye sanitización servidor |
| **CSS Strategy** | **CSS Custom Properties nativas** | Sin Node.js, sin PostCSS, sin build step, misma potencia de tokens |
| **Iconos** | **SVG inline** | Performance, control total, sin dependencias |
| **Rate limiting** | **No en Fase 2** | Documentado como `SECURITY-01` para pre-producción |
| **Inter font** | **Google Fonts en prototipos, local en prod** | Privacidad, rendimiento, control de versiones |

---

## 8. Dependencias a añadir en `pyproject.toml`

```toml
[project]
dependencies = [
    "django[argon2]>=6.1.3",
    "markdown-it-py>=3.0.0",
    "nh3>=0.2.18",
    "easymde>=2.21.0",  # solo para archivos estáticos locales; no es dependencia Python
]
```

> **Nota**: `easymde` no es paquete Python — se descargan sus archivos JS/CSS a `static/vendor/easymde/` y se sirven como estáticos.

---

## 9. Integración con accounts (Fase 1)

### 9.1 Cambios visuales login/registro

- `base.html` → nueva versión dark-first Gentle-AI
- Cards con `bg-card`, bordes `border`
- Inputs con `bg-card`, focus ring `accent`
- Botones: primary (magenta), ghost (secundario)
- Tipografía Inter, spacing 4px grid
- Navbar sticky con backdrop-blur
- Footer simplificado

### 9.2 Comportamiento inalterado

- Rutas: `/cuentas/login/`, `/cuentas/registro/`, `/cuentas/logout/`
- Backends: `EmailOrUsernameModelBackend`
- Formularios: `CustomUserCreationForm`, `EmailOrUsernameAuthenticationForm`
- CSRF, sesiones, validaciones idénticas
- Redirects: login → tasks:list, logout → accounts:login

---

## 10. Estado de T1 — Foundation

| Archivo | Estado | Observaciones |
|---|---|---|
| `design-tokens.css` | ✅ Completado | Tokens actualizados tras auditoría contraste |
| `global.css` | ✅ Completado | Reset, base, utilities |
| `components.css` | ✅ Completado | Badges corregidos con texto oscuro |
| `layout.css` | ✅ Completado | Sidebar, navbar, dialogs, responsive |
| `markdown.css` | ✅ Completado | Editor, preview, split view, tabs |
| Integración templates | ⏳ Pendiente | Actualizar `base.html` accounts + crear `base.html` tasks |

**Conclusión T1**: **Parcialmente completado** — CSS listo, falta integración en templates Django.

---

## 11. Revisión de prototipos

| Prototipo | Coherencia Gentle-AI | Jerarquía | Contraste | Navegación | Diálogos | Interacciones | Responsive | Accesibilidad | Sidebar | Toolbar MD | Estados |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `login.html` | ✅ | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | N/A | N/A | ✅ |
| `register.html` | ✅ | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | N/A | N/A | ✅ |
| `task-list.html` | ✅ | ✅ | ✅ | ✅ | ✅ Search | ✅ | ✅ | ✅ | N/A | N/A | ✅ |
| `task-detail.html` | ✅ | ✅ | ✅ | ✅ | N/A | ✅ Resize | ✅ | ✅ | ✅ Resize + drawer | N/A | ✅ |
| `markdown-editor.html` | ✅ | ✅ | ✅ | ✅ | ✅ Preview | ✅ Toolbar + shortcuts | ✅ | ✅ | N/A | ✅ 11 actions | ✅ |

**Observaciones:**
- Todos usan tokens CSS variables, fuentes Inter, dark-first
- Badges en prototipos usan colores corregidos (texto oscuro)
- Search dialog nativo `<dialog>` con focus trap y Escape
- Sidebar resize: mouse drag + keyboard arrows + mobile drawer
- Markdown editor: toolbar 11 acciones, shortcuts Ctrl+, preview modal
- Estados de error/guardado representados en componentes

---

## 12. Riesgos pendientes

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **EasyMDE mantenimiento** | Medio | CodeMirror 5 legacy; migración a CodeMirror 6 en fase futura si necesario |
| **nh3 compatibilidad** | Bajo | Rust + PyO3; verificar wheels en CI para Linux/macOS/Windows |
| **Sanitización consistente** | Alto | Función única `render_markdown_safe()` compartida por vista + preview |
| **Sidebar resize móvil** | Bajo | Drawer off-canvas implementado; probar en dispositivos reales |
| **Búsqueda performance** | Bajo | Solo title+body en Fase 2; añadir índice FTS5 en SQLite si necesario |
| **Multi-select coautores** | Bajo | `<select multiple>` nativo + enhancement JS; fallback accesible |

---

## 13. Próximos pasos

1. ✅ Documento de feature (`odd/tasks/tasks-core.md`)
2. ✅ Design system documentado (`design/system.md`) — **actualizado con auditoría**
3. ✅ CSS global creado (5 archivos) — **tokens corregidos**
4. ✅ Prototipos HTML (5) — **revisados y coherentes**
5. ⏳ **Actualizar `pyproject.toml` con nuevas dependencias**
6. ⏳ **Integrar CSS en templates Django** (accounts + tasks)
7. ⏳ Aprobar para comenzar implementación T2-T14