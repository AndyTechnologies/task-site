"""
Utilidades para Tasks.

Centraliza el renderizado seguro de Markdown con sanitización.
"""
from markdown_it import MarkdownIt
import nh3


# Configuración de markdown-it-py
_md_parser = MarkdownIt(
    "commonmark",
    {
        "html": False,  # Deshabilitar HTML arbitrario
        "linkify": True,
        "typographer": True,
    }
).enable(["table", "strikethrough"])


# Configuración de nh3 (allowlist)
_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "ul", "ol", "li",
    "strong", "em", "u", "s",
    "code", "pre",
    "blockquote",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "input",  # para task lists
}

_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "input": {"type", "checked", "disabled"},
    "th": {"scope"},
    "td": {"colspan", "rowspan"},
}

_ALLOWED_URL_SCHEMES = {"http", "https", "mailto", "tel"}


def render_markdown_safe(markdown_text: str) -> str:
    """
    Renderiza Markdown a HTML seguro.

    Pipeline:
    1. markdown-it-py: parse CommonMark -> HTML (sin HTML arbitrario)
    2. nh3: sanitiza HTML con allowlist estricta

    Args:
        markdown_text: Texto en Markdown

    Returns:
        HTML sanitizado seguro para renderizar
    """
    if not markdown_text:
        return ""

    # Paso 1: Parsear Markdown a HTML (sin HTML arbitrario en input)
    html = _md_parser.render(markdown_text)

    # Paso 2: Sanitizar con nh3 (allowlist estricta)
    clean_html = nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        strip_comments=True,
        link_rel=None,  # Permitir gestión manual de rel
    )

    return clean_html


def render_markdown_preview(markdown_text: str) -> str:
    """
    Versión para vista previa en editor (igual que render_markdown_safe).

    Mantiene la misma política de seguridad para consistencia.

    Args:
        markdown_text: Texto en Markdown

    Returns:
        HTML sanitizado
    """
    return render_markdown_safe(markdown_text)