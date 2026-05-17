from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import ValidationError
from sqlmodel import Session, select

from app.database import get_session
from app.models import Lead
from app.schemas import LeadCreate
from app.services.ai_service import generate_ai_report_content
from app.services.email_service import send_report_email
from app.services.enrichment_service import enrich_company
from app.services.pdf_service import generate_pdf_report
from app.services.sheets_service import append_lead_to_sheet


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


@router.get("/form", response_class=HTMLResponse)
def show_lead_form(request: Request):
    """
    Display the lead intake form.

    This is the public entry point where a prospect submits their details.
    """
    return request.app.state.templates.TemplateResponse(
        "lead_form.html",
        {
            "request": request,
            "error": None,
            "form_data": {},
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def leads_dashboard(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Display a simple internal dashboard of submitted leads.

    This helps reviewers/demo users inspect the full workflow:
    - submitted leads,
    - enrichment status,
    - AI generation status,
    - PDF generation status,
    - email delivery status,
    - Google Sheets logging status,
    - errors/fallback notes.
    """

    statement = select(Lead).order_by(Lead.created_at.desc())
    leads = session.exec(statement).all()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "leads": leads,
        },
    )


@router.get("/{lead_id}/download-report")
def download_report(
    lead_id: int,
    session: Session = Depends(get_session),
):
    """
    Download the generated PDF report for a lead.

    This route makes generated reports accessible from the dashboard
    without exposing the entire generated_reports directory as static files.
    """

    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not lead.report_file_path:
        raise HTTPException(
            status_code=404,
            detail="No report has been generated for this lead.",
        )

    report_path = Path(lead.report_file_path)

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file does not exist on the server.",
        )

    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=report_path.name,
    )


@router.post("/submit", response_class=HTMLResponse)
def submit_lead(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    company_name: str = Form(...),
    company_website: str = Form(...),
    industry: str = Form(""),
    message: str = Form(""),
    session: Session = Depends(get_session),
):
    """
    Complete lead intake workflow.

    Workflow:
    1. Validate submitted form data.
    2. Store the lead in SQLite.
    3. Enrich company information using the submitted website.
    4. Generate structured AI/fallback audit content.
    5. Generate a professional PDF report.
    6. Send the PDF report by email if SMTP is configured.
    7. Log the processed lead to Google Sheets if configured.
    8. Update the lead with final workflow status.
    """

    form_data = {
        "full_name": full_name,
        "email": email,
        "company_name": company_name,
        "company_website": company_website,
        "industry": industry,
        "message": message,
    }

    try:
        validated_lead = LeadCreate(
            full_name=full_name,
            email=email,
            company_name=company_name,
            company_website=company_website,
            industry=industry or None,
            message=message or None,
        )

    except ValidationError as exc:
        return request.app.state.templates.TemplateResponse(
            "lead_form.html",
            {
                "request": request,
                "error": exc.errors()[0]["msg"],
                "form_data": form_data,
            },
            status_code=400,
        )

    lead = Lead(
        full_name=validated_lead.full_name,
        email=str(validated_lead.email),
        company_name=validated_lead.company_name,
        company_website=str(validated_lead.company_website),
        industry=validated_lead.industry,
        message=validated_lead.message,
        report_status="received",
        enrichment_status="pending",
        ai_generation_status="pending",
        email_status="pending",
        sheets_status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    session.add(lead)
    session.commit()
    session.refresh(lead)

    # Step 1: Company enrichment
    enrichment_result = enrich_company(
        company_name=lead.company_name,
        company_website=lead.company_website,
        industry=lead.industry,
        message=lead.message,
    )

    lead.enrichment_status = enrichment_result.get("status", "fallback")
    lead.website_title = enrichment_result.get("title")
    lead.website_meta_description = enrichment_result.get("meta_description")
    lead.website_headings = enrichment_result.get("headings")
    lead.website_summary_text = enrichment_result.get("summary_text")
    lead.detected_keywords = enrichment_result.get("keywords")

    if enrichment_result.get("error"):
        lead.error_message = enrichment_result.get("error")

    lead.updated_at = datetime.now(timezone.utc)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    # Step 2: AI/fallback report content generation
    lead_data = {
        "id": lead.id,
        "full_name": lead.full_name,
        "email": lead.email,
        "company_name": lead.company_name,
        "company_website": lead.company_website,
        "industry": lead.industry,
        "message": lead.message,
    }

    enrichment_data = {
        "website_title": lead.website_title,
        "website_meta_description": lead.website_meta_description,
        "website_headings": lead.website_headings,
        "website_summary_text": lead.website_summary_text,
        "detected_keywords": lead.detected_keywords,
    }

    report_content = generate_ai_report_content(
        lead_data=lead_data,
        enrichment_data=enrichment_data,
    )

    lead.ai_generation_status = report_content.get("status", "fallback")
    lead.executive_summary = report_content.get("executive_summary")
    lead.company_overview = report_content.get("company_overview")
    lead.observed_positioning = report_content.get("observed_positioning")
    lead.potential_pain_points = report_content.get("potential_pain_points")
    lead.automation_opportunities = report_content.get("automation_opportunities")
    lead.recommended_workflow = report_content.get("recommended_workflow")
    lead.next_steps = report_content.get("next_steps")
    lead.personalized_email_body = report_content.get("personalized_email_body")
    lead.report_status = "content_generated"

    if report_content.get("error"):
        existing_error = lead.error_message or ""
        lead.error_message = (
            f"{existing_error} | AI fallback reason: {report_content.get('error')}"
        ).strip(" |")

    lead.updated_at = datetime.now(timezone.utc)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    # Step 3: PDF generation
    try:
        report_data = {
            "executive_summary": lead.executive_summary,
            "company_overview": lead.company_overview,
            "observed_positioning": lead.observed_positioning,
            "potential_pain_points": lead.potential_pain_points,
            "automation_opportunities": lead.automation_opportunities,
            "recommended_workflow": lead.recommended_workflow,
            "next_steps": lead.next_steps,
        }

        pdf_path = generate_pdf_report(
            lead_data=lead_data,
            report_data=report_data,
        )

        lead.report_file_path = pdf_path
        lead.report_status = "pdf_generated"

    except Exception as exc:
        lead.report_status = "pdf_failed"
        existing_error = lead.error_message or ""
        lead.error_message = (
            f"{existing_error} | PDF generation failed: {str(exc)}"
        ).strip(" |")

    lead.updated_at = datetime.now(timezone.utc)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    # Step 4: Email delivery
    if lead.report_status == "pdf_generated" and lead.report_file_path:
        email_result = send_report_email(
            recipient_email=lead.email,
            full_name=lead.full_name,
            company_name=lead.company_name,
            pdf_path=lead.report_file_path,
            email_body=lead.personalized_email_body,
        )

        lead.email_status = email_result.get("status", "failed")

        if lead.email_status == "sent":
            lead.report_status = "email_sent"
            lead.email_sent_at = datetime.now(timezone.utc)

        elif lead.email_status == "skipped":
            lead.report_status = "email_skipped"
            existing_error = lead.error_message or ""
            lead.error_message = (
                f"{existing_error} | Email skipped: {email_result.get('error')}"
            ).strip(" |")

        else:
            lead.report_status = "email_failed"
            existing_error = lead.error_message or ""
            lead.error_message = (
                f"{existing_error} | Email failed: {email_result.get('error')}"
            ).strip(" |")

    else:
        lead.email_status = "skipped"

    # Step 5: Google Sheets logging
    sheets_result = append_lead_to_sheet(
        lead_data={
            "full_name": lead.full_name,
            "email": lead.email,
            "company_name": lead.company_name,
            "company_website": lead.company_website,
            "report_status": lead.report_status,
            "email_status": lead.email_status,
        }
    )

    lead.sheets_status = sheets_result.get("status", "failed")

    if lead.sheets_status == "logged":
        lead.sheets_logged_at = datetime.now(timezone.utc)

    elif lead.sheets_status == "skipped":
        existing_error = lead.error_message or ""
        lead.error_message = (
            f"{existing_error} | Sheets skipped: {sheets_result.get('error')}"
        ).strip(" |")

    else:
        existing_error = lead.error_message or ""
        lead.error_message = (
            f"{existing_error} | Sheets failed: {sheets_result.get('error')}"
        ).strip(" |")

    lead.updated_at = datetime.now(timezone.utc)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    return request.app.state.templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "lead": lead,
        },
    )