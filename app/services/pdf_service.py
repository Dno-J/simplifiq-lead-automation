import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi.templating import Jinja2Templates
from weasyprint import HTML

from app.config import settings


templates = Jinja2Templates(directory="app/templates")


def slugify(value: str) -> str:
    """
    Convert company names into safe file-name strings.

    Example:
    "Acme Finance Pvt Ltd" -> "acme-finance-pvt-ltd"
    """
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "company"


def ensure_report_directory() -> Path:
    """
    Ensure the generated report output directory exists.
    """
    output_dir = Path(settings.REPORT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_report_filename(company_name: str, lead_id: int) -> str:
    """
    Build a unique PDF file name for each generated lead report.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    company_slug = slugify(company_name)

    return f"ai-audit-{company_slug}-lead-{lead_id}-{timestamp}.pdf"


def generate_pdf_report(
    lead_data: Dict[str, Any],
    report_data: Dict[str, Any],
) -> str:
    """
    Generate a professional PDF report from lead and audit content.

    Returns:
        str: Path to the generated PDF file.
    """

    output_dir = ensure_report_directory()

    lead_id = lead_data.get("id")
    company_name = lead_data.get("company_name", "Company")

    file_name = build_report_filename(
        company_name=company_name,
        lead_id=lead_id,
    )

    file_path = output_dir / file_name

    template = templates.get_template("report_template.html")

    rendered_html = template.render(
        lead=lead_data,
        report=report_data,
        generated_at=datetime.utcnow().strftime("%d %B %Y"),
    )

    HTML(string=rendered_html, base_url=os.getcwd()).write_pdf(str(file_path))

    return str(file_path)