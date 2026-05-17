import json
from typing import Any, Dict

from openai import OpenAI

from app.config import settings


def _safe_join_list(items: list[str]) -> str:
    """
    Convert a list of strings into a clean bullet-like plain text section.
    """
    return "\n".join(f"- {item}" for item in items if item)


def build_fallback_report_content(
    lead_data: Dict[str, Any],
    enrichment_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate a practical rule-based report when an AI API key is unavailable
    or the AI call fails.

    This keeps the full workflow functional for local testing and review.
    """

    company_name = lead_data.get("company_name", "the company")
    industry = lead_data.get("industry") or "their industry"
    message = lead_data.get("message") or ""
    keywords = enrichment_data.get("detected_keywords") or "lead management, operations, automation"
    website_summary = enrichment_data.get("website_summary_text") or ""
    meta_description = enrichment_data.get("website_meta_description") or ""

    business_context = meta_description or website_summary[:500]

    if not business_context:
        business_context = (
            f"{company_name} appears to be operating in {industry}. "
            "The website did not provide enough structured public information, "
            "so this audit focuses on common automation opportunities for similar businesses."
        )

    pain_points = [
        "Manual follow-up after lead submission can delay response time.",
        "Sales or operations teams may spend unnecessary time researching each prospect manually.",
        "Lead qualification may depend on inconsistent human judgment.",
        "Personalized outreach can become difficult to scale as inquiry volume increases.",
    ]

    if message:
        pain_points.insert(
            0,
            f"The prospect specifically mentioned this area of interest: {message}",
        )

    opportunities = [
        "Automated lead enrichment using company websites and public data sources.",
        "AI-generated first-touch audit reports personalized for each prospect.",
        "Lead scoring based on industry, company profile, and submitted intent.",
        "Automated email follow-up with relevant recommendations and next steps.",
        "Internal dashboard for tracking report generation, delivery status, and lead quality.",
    ]

    workflow = [
        "Lead submits company details through an intake form.",
        "The system validates the lead and stores it in a database.",
        "Company data is enriched from the submitted website.",
        "AI generates a personalized audit and business recommendations.",
        "A professional PDF report is generated and emailed automatically.",
        "The lead is logged for sales or consulting follow-up.",
    ]

    next_steps = [
        "Review the highest-friction manual steps in the current lead follow-up process.",
        "Define lead qualification criteria such as company size, industry, urgency, and service fit.",
        "Start with one automation workflow: lead intake, enrichment, report generation, and email delivery.",
        "Track report opens, replies, and booked calls to measure impact.",
    ]

    email_body = (
        f"Hi {lead_data.get('full_name', 'there')},\n\n"
        f"Thank you for sharing details about {company_name}. "
        "We prepared a short AI opportunity audit based on your submitted information "
        "and the publicly available context from your company website.\n\n"
        "The attached report highlights possible automation opportunities around lead intake, "
        "qualification, research, and personalized follow-up.\n\n"
        "Best,\n"
        "SimplifiQ Team"
    )

    return {
        "status": "fallback",
        "executive_summary": (
            f"{company_name} can improve its first-response and lead handling process by using "
            "AI to automate research, qualification, report generation, and personalized outreach. "
            f"Based on the available context, the strongest opportunity is to reduce manual effort "
            f"while creating a more tailored experience for prospects in {industry}."
        ),
        "company_overview": (
            f"{company_name} was submitted as a prospect in the {industry} space. "
            f"Relevant public/contextual signals include: {business_context}"
        ),
        "observed_positioning": (
            f"The available website context and keywords suggest themes around: {keywords}. "
            "The company can benefit from clearer mapping between customer intent, business needs, "
            "and automated follow-up actions."
        ),
        "potential_pain_points": _safe_join_list(pain_points),
        "automation_opportunities": _safe_join_list(opportunities),
        "recommended_workflow": _safe_join_list(workflow),
        "next_steps": _safe_join_list(next_steps),
        "personalized_email_body": email_body,
    }


def build_ai_prompt(
    lead_data: Dict[str, Any],
    enrichment_data: Dict[str, Any],
) -> str:
    """
    Build a structured prompt for report generation.

    The model is asked to return JSON so the application can control
    formatting and PDF layout separately.
    """

    return f"""
You are an AI business consultant working for SimplifiQ.

Generate a professional, highly personalized AI opportunity audit for the following prospect.

Lead Details:
- Full Name: {lead_data.get("full_name")}
- Email: {lead_data.get("email")}
- Company Name: {lead_data.get("company_name")}
- Company Website: {lead_data.get("company_website")}
- Industry: {lead_data.get("industry")}
- Prospect Message: {lead_data.get("message")}

Website Enrichment:
- Website Title: {enrichment_data.get("website_title")}
- Meta Description: {enrichment_data.get("website_meta_description")}
- Headings: {enrichment_data.get("website_headings")}
- Detected Keywords: {enrichment_data.get("detected_keywords")}
- Website Text Summary: {enrichment_data.get("website_summary_text")}

Write the report as if it will be delivered directly to the prospect.
Keep it professional, specific, and practical.
Do not invent fake statistics, fake clients, funding, revenue, or team size.

Return ONLY valid JSON with these exact keys:
{{
  "executive_summary": "...",
  "company_overview": "...",
  "observed_positioning": "...",
  "potential_pain_points": "- ...\\n- ...\\n- ...",
  "automation_opportunities": "- ...\\n- ...\\n- ...",
  "recommended_workflow": "- ...\\n- ...\\n- ...",
  "next_steps": "- ...\\n- ...\\n- ...",
  "personalized_email_body": "..."
}}
"""


def generate_ai_report_content(
    lead_data: Dict[str, Any],
    enrichment_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate structured report content.

    Uses OpenAI when OPENAI_API_KEY is configured.
    Falls back to rule-based content when unavailable or when the call fails.
    """

    if not settings.OPENAI_API_KEY:
        return build_fallback_report_content(
            lead_data=lead_data,
            enrichment_data=enrichment_data,
        )

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = build_ai_prompt(
            lead_data=lead_data,
            enrichment_data=enrichment_data,
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate concise, practical, professional AI opportunity audits. "
                        "You must return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
        )

        raw_content = response.choices[0].message.content or ""
        parsed_content = json.loads(raw_content)

        required_keys = [
            "executive_summary",
            "company_overview",
            "observed_positioning",
            "potential_pain_points",
            "automation_opportunities",
            "recommended_workflow",
            "next_steps",
            "personalized_email_body",
        ]

        for key in required_keys:
            if key not in parsed_content:
                parsed_content[key] = ""

        parsed_content["status"] = "success"
        return parsed_content

    except Exception as exc:
        fallback = build_fallback_report_content(
            lead_data=lead_data,
            enrichment_data=enrichment_data,
        )
        fallback["status"] = "fallback"
        fallback["error"] = str(exc)
        return fallback