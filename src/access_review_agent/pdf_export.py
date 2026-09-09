"""Aggregate report PDF export (SPEC.md §6, Milestone 11): a mechanical
rendering step, no reasoning in it - Markdown -> HTML -> PDF, pure Python
(no system dependencies like Cairo/Pango, unlike WeasyPrint), so it works
identically locally and in CI with no extra setup. Renders the aggregate
report's own already-generated Markdown content directly, not a separate
hand-authored template - one source of truth for content; the PDF is
just another rendering of it, the same relationship commit_report's
Markdown files already have to their own source data.
"""

import io

import markdown
from xhtml2pdf import pisa


def render_pdf(markdown_content: str) -> bytes:
    html = markdown.markdown(markdown_content, extensions=["tables"])
    buf = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buf)
    if result.err:
        raise RuntimeError(f"PDF generation failed with {result.err} error(s)")
    return buf.getvalue()
