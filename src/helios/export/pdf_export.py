"""PDF report export using WeasyPrint and Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template
from weasyprint import HTML  # type: ignore[import-untyped]

from helios.core.audit_record import AuditRecord


def export_pdf(record: AuditRecord, output_path: Path) -> Path:
    """Render an audit record into a human-readable PDF report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = Template(
        """
        <html>
        <body>
            <h1>HELIOS Compliance Report</h1>
            <p><strong>Run ID:</strong> {{ run_id }}</p>
            <p><strong>Pipeline:</strong> {{ pipeline_name }}</p>
            <p><strong>Executor:</strong> {{ executor }}</p>
            <h2>Checks</h2>
            <ul>
            {% for check in checks %}
                <li>{{ check.check_id }} - {{ check.status }}: {{ check.message }}</li>
            {% endfor %}
            </ul>
        </body>
        </html>
        """
    )
    html = template.render(
        run_id=str(record.run_id),
        pipeline_name=record.pipeline_name,
        executor=record.executor,
        checks=[check.model_dump() for check in record.checks],
    )
    HTML(string=html).write_pdf(str(output_path))
    return output_path

