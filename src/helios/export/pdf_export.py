"""PDF report export using WeasyPrint and Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML  # type: ignore[import-untyped]

from helios import __version__
from helios.checks import CheckRegistry
from helios.core.audit_record import AuditRecord


def export_pdf(record: AuditRecord, output_path: Path) -> Path:
    """Render an audit record into a human-readable PDF report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("compliance_report.html.j2")
    score = CheckRegistry().compute_score(record.checks)
    html = template.render(
        record=record,
        score=score,
        checks=record.checks,
        version=__version__,
        now=record.end_time or record.start_time,
    )
    HTML(string=html).write_pdf(str(output_path))
    return output_path
