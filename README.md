# SimplifiQ Lead Automation

An AI-powered lead intake and follow-up automation prototype built for the **SimplifiQ AI Software Developer Intern Assessment**.

The system captures prospect details, enriches company information from the submitted website, generates a personalized AI opportunity audit, creates a PDF report, attempts email delivery, and optionally logs lead data to Google Sheets.

---

## Problem Statement

Many businesses rely on lead intake forms to capture potential client information. However, the follow-up process is often manual: teams research the company, prepare insights, create audit notes, and send personalized outreach emails.

This project automates that workflow end-to-end.

When a prospect submits a form, the system automatically:

1. Captures and validates lead information
2. Enriches company data using the submitted website
3. Generates a personalized audit/report
4. Creates a professional PDF document
5. Attempts to email the report to the prospect
6. Tracks the workflow status in a local dashboard
7. Optionally logs the lead to Google Sheets

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Code Organization](#code-organization)
- [Workflow](#workflow)
- [Status Tracking](#status-tracking)
- [Setup Instructions](#setup-instructions)
- [How to Test the Workflow](#how-to-test-the-workflow)
- [Main Routes](#main-routes)
- [AI Report Generation](#ai-report-generation)
- [Email Delivery](#email-delivery)
- [Google Sheets Logging](#google-sheets-logging)
- [PDF Reports](#pdf-reports)
- [Dashboard](#dashboard)
- [Error Handling and Fallbacks](#error-handling-and-fallbacks)
- [Assumptions](#assumptions)
- [Tradeoffs](#tradeoffs)
- [Security Notes](#security-notes)
- [Production Improvements](#production-improvements)
- [Local Testing Checklist](#local-testing-checklist)
- [Deployment Note](#deployment-note)
- [Final Notes](#final-notes)

## Core Features

- Lead intake form with backend validation
- SQLite-based lead storage
- Website scraping and company enrichment
- AI-generated audit content using OpenAI
- Rule-based fallback report generation when AI is unavailable
- Professional PDF report generation
- Email delivery with PDF attachment
- Safe email fallback when SMTP is not configured
- Internal admin dashboard for reviewing submitted leads
- PDF download route
- Optional Google Sheets lead logging
- Status and error tracking across the workflow

---

## Tech Stack

- **Backend:** FastAPI
- **Templating:** Jinja2
- **Database:** SQLite with SQLModel
- **Validation:** Pydantic
- **Website Enrichment:** Requests + BeautifulSoup
- **AI Report Generation:** OpenAI API with fallback mode
- **PDF Generation:** WeasyPrint
- **Email:** SMTP
- **Bonus Logging:** Google Sheets API
- **Server:** Uvicorn

---

## Project Structure

```text
simplifiq-lead-automation/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── leads.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── enrichment_service.py
│   │   ├── ai_service.py
│   │   ├── pdf_service.py
│   │   ├── email_service.py
│   │   └── sheets_service.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── lead_form.html
│   │   ├── success.html
│   │   ├── dashboard.html
│   │   └── report_template.html
│   │
│   └── static/
│       └── styles.css
│
├── generated_reports/
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
````

---

## Code Organization

The project is organized around a simple FastAPI service-layer structure.

### Application Core

- `app/main.py`  
  Creates the FastAPI application, mounts static files, initializes templates, registers routers, and creates database tables during startup.

- `app/config.py`  
  Loads environment variables such as database URL, OpenAI key, SMTP settings, report output directory, and Google Sheets configuration.

- `app/database.py`  
  Configures the SQLModel engine and provides the database session dependency used by routes.

- `app/models.py`  
  Defines the `Lead` database model, including submitted lead data, enrichment results, generated report content, PDF path, email status, Sheets status, and timestamps.

- `app/schemas.py`  
  Defines Pydantic validation schemas for lead submission.

### Routing Layer

- `app/routers/leads.py`  
  Contains the main lead workflow routes:
  - lead form
  - lead submission
  - dashboard
  - PDF download

  The submission route coordinates validation, enrichment, AI/fallback content generation, PDF creation, email delivery, Google Sheets logging, and status updates.

### Service Layer

- `app/services/enrichment_service.py`  
  Scrapes the submitted company website and extracts title, meta description, headings, readable page text, and keywords. Includes fallback behavior if scraping fails.

- `app/services/ai_service.py`  
  Generates structured audit report content using OpenAI when configured. If OpenAI is unavailable, quota-limited, or not configured, it uses a rule-based fallback generator.

- `app/services/pdf_service.py`  
  Renders the report template and generates a PDF file in the configured report output directory.

- `app/services/email_service.py`  
  Sends the generated PDF report by SMTP when credentials are configured. Skips safely when email settings are missing.

- `app/services/sheets_service.py`  
  Optionally appends processed lead data to Google Sheets using a service account. Skips safely when disabled or not configured.

### Templates and Static Files

- `app/templates/lead_form.html`  
  Public lead intake form.

- `app/templates/success.html`  
  Displays the result of a completed workflow.

- `app/templates/dashboard.html`  
  Internal dashboard showing submitted leads, statuses, PDF download links, and errors.

- `app/templates/report_template.html`  
  HTML template used to generate the PDF report.

- `app/static/styles.css`  
  Styling for the lead form, dashboard, success page, and UI components.

## Workflow

```text
Prospect submits lead form
        ↓
FastAPI validates input
        ↓
Lead is saved to SQLite
        ↓
Company website is scraped/enriched
        ↓
AI or fallback report content is generated
        ↓
PDF audit report is created
        ↓
Email delivery is attempted
        ↓
Google Sheets logging is attempted if enabled
        ↓
Dashboard shows workflow status
```

---

## Status Tracking

Each lead stores workflow statuses such as:

```text
report_status
email_status
sheets_status
enrichment_status
ai_generation_status
```

Example statuses:

```text
received
content_generated
pdf_generated
email_sent
email_skipped
email_failed
logged
skipped
fallback
success
failed
```

This makes the system easier to debug and demonstrate.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd simplifiq-lead-automation
```

### 2. Create Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 5. Configure `.env`

For basic local testing, API credentials are optional.

```env
APP_NAME="SimplifiQ Lead Automation"
APP_ENV="development"
DATABASE_URL="sqlite:///./simplifiq_leads.db"

OPENAI_API_KEY=""

SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME=""
SMTP_PASSWORD=""
SMTP_FROM_EMAIL=""

REPORT_OUTPUT_DIR="generated_reports"

GOOGLE_SHEETS_ENABLED=false
GOOGLE_SERVICE_ACCOUNT_FILE="google_service_account.json"
GOOGLE_SHEET_ID=""
GOOGLE_SHEET_RANGE="Leads!A:G"
```

With this configuration:

* AI generation uses fallback mode
* PDF generation still works
* Email delivery is skipped safely
* Google Sheets logging is skipped safely

### 6. Run the Application

Option 1:

```bash
python run.py
```

Option 2:

```bash
uvicorn app.main:app --reload
```

Open the lead form:

```text
http://127.0.0.1:8000/leads/form
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Dashboard:

```text
http://127.0.0.1:8000/leads/dashboard
```

---

## How to Test the Workflow

Submit a lead using:

```text
Full Name: Dino Jackson
Email: jacksondino00@gmail.com
Company Name: LendingIQ
Company Website: https://www.lendingiq.ai/
Industry: Finance / Lending
Message: We want to automate lead qualification and client follow-up.
```

Expected local result without API/email/Google credentials:

```text
Enrichment Status: success
AI Generation Status: fallback
Report Status: email_skipped
Email Status: skipped
Sheets Status: skipped
PDF generated successfully
```

The generated PDF can be downloaded from:

```text
http://127.0.0.1:8000/leads/dashboard
```

---

## Main Routes

```text
GET  /
GET  /health
GET  /leads/form
POST /leads/submit
GET  /leads/dashboard
GET  /leads/{lead_id}/download-report
```

---

## AI Report Generation

The system uses OpenAI when `OPENAI_API_KEY` is configured.

If the API key is missing, quota-limited, or the API call fails, the system automatically falls back to a rule-based report generator.

This ensures that the workflow remains functional during review.

### AI Mode

```env
OPENAI_API_KEY="your_openai_api_key"
```

### Fallback Mode

```env
OPENAI_API_KEY=""
```

Fallback mode still generates:

* Executive summary
* Company overview
* Observed positioning
* Potential pain points
* AI automation opportunities
* Recommended workflow
* Next steps
* Email body

---

## Email Delivery

Email delivery uses SMTP.

For Gmail, use a Gmail App Password instead of your normal Gmail password.

Example:

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your_email@gmail.com"
SMTP_PASSWORD="your_16_character_app_password"
SMTP_FROM_EMAIL="your_email@gmail.com"
```

If SMTP credentials are missing, email delivery is skipped safely and the system still generates the PDF.

Expected skipped status:

```text
Email Status: skipped
Report Status: email_skipped
```

---

## Google Sheets Logging

Google Sheets logging is optional bonus functionality.

When enabled, the app appends each processed lead to a Google Sheet with:

```text
Timestamp
Name
Email
Company
Website
Report Status
Email Status
```

### Google Sheets Setup Steps

1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account
4. Download the service account JSON file
5. Rename it:

```text
google_service_account.json
```

6. Place it in the project root
7. Copy the `client_email` from the JSON file
8. Share your Google Sheet with that service account email as Editor
9. Add the Sheet ID to `.env`

```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SERVICE_ACCOUNT_FILE="google_service_account.json"
GOOGLE_SHEET_ID="your_google_sheet_id"
GOOGLE_SHEET_RANGE="Leads!A:G"
```

The first row of the sheet should be:

```text
Timestamp | Name | Email | Company | Website | Report Status | Email Status
```

If Google Sheets is disabled or not configured, the workflow continues safely.

Expected skipped status:

```text
Sheets Status: skipped
```

Expected successful status:

```text
Sheets Status: logged
```

---

## PDF Reports

Generated reports are saved locally in:

```text
generated_reports/
```

Example filename:

```text
ai-audit-lendingiq-lead-1-20260517145011.pdf
```

PDFs can be downloaded through the dashboard using:

```text
/leads/{lead_id}/download-report
```

The app does not expose the entire reports folder as a public static directory. Instead, reports are served through a lead-specific download route.

---

## Dashboard

The internal dashboard is available at:

```text
http://127.0.0.1:8000/leads/dashboard
```

It shows:

* Lead details
* Company details
* Report status
* Email status
* Google Sheets status
* Enrichment status
* AI generation status
* PDF download link
* Error/fallback notes
* Created timestamp

---

## Error Handling and Fallbacks

The project includes practical fallback handling for real-world scenarios.

### Website Scraping Failure

If scraping fails, the app creates fallback enrichment using submitted lead details.

Example:

```text
enrichment_status = fallback
```

### AI API Failure

If OpenAI is unavailable, quota-limited, or not configured, the app uses rule-based report generation.

Example:

```text
ai_generation_status = fallback
```

### PDF Generation Failure

If PDF creation fails, the lead is marked as:

```text
report_status = pdf_failed
```

The error is stored in the dashboard.

### Email Failure

If SMTP is not configured, the app marks email as:

```text
email_status = skipped
report_status = email_skipped
```

If SMTP fails, it marks:

```text
email_status = failed
report_status = email_failed
```

### Google Sheets Failure

If Google Sheets is disabled or credentials are missing:

```text
sheets_status = skipped
```

If the Sheets API fails:

```text
sheets_status = failed
```

---

## Assumptions

* The submitted website is publicly accessible.
* The homepage contains enough public text for basic enrichment.
* The prototype can run synchronously for assessment purposes.
* SMTP and Google Sheets credentials may not be available to reviewers.
* OpenAI API access may be missing or quota-limited, so fallback mode is required.
* SQLite is sufficient for local demonstration.
* The dashboard is intended for internal review/demo use only.

---

## Tradeoffs

### Synchronous Workflow

The entire workflow currently runs during form submission.

This is simple and easy to review, but in production it should be moved to a background worker queue such as Celery, RQ, Dramatiq, or a managed task queue.

### SQLite Database

SQLite keeps setup simple for assessment review.

In production, PostgreSQL would be preferred.

### Website Scraping

The enrichment service uses simple public website scraping.

Some websites may block requests, render content through JavaScript, or provide limited content. In those cases, fallback enrichment is used.

### PDF Storage

PDFs are stored locally in `generated_reports/`.

In production, generated reports should be archived in cloud storage such as Google Drive, S3, or similar.

### Basic Admin Dashboard

The dashboard is intentionally lightweight and does not include authentication.

In production, it should be protected with admin authentication.

### Optional Integrations

OpenAI, SMTP, and Google Sheets are optional for local review.

This decision allows reviewers to run the project without private credentials while still seeing the full workflow and fallback behavior.

---

## Security Notes

Do not commit these files to GitHub:

```text
.env
google_service_account.json
simplifiq_leads.db
generated_reports/
```

These are included in `.gitignore`.

Never expose:

* API keys
* SMTP passwords
* Google service account credentials
* Generated customer reports
* Local database files

---

## Production Improvements

Given more time, the following improvements would be added:

* Background queue for report generation and email delivery
* PostgreSQL database
* Admin authentication
* Retry logic for enrichment, email, and Sheets logging
* Better duplicate lead detection
* CRM integration
* Google Drive PDF archiving
* Cloud deployment on Render
* Dockerfile and deployment configuration
* More advanced AI prompt evaluation
* Unit and integration tests
* Better report template customization by industry
* Async workflow updates through polling or WebSockets
* Better observability with structured logs

---

## Local Testing Checklist

Before submitting, verify:

```text
Lead form loads
Lead submission works
Lead is saved to SQLite
Website enrichment runs
AI fallback works if no API key is configured
PDF is generated
PDF download works from dashboard
Email is skipped safely if SMTP is not configured
Sheets logging is skipped safely if disabled
Dashboard shows statuses and error notes
```

Run:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:8000/leads/form
```

Submit a test lead and check:

```text
http://127.0.0.1:8000/leads/dashboard
```

---
## Deployment Note

A live demo is not included because the workflow depends on private credential-based integrations such as OpenAI, SMTP email delivery, and Google Sheets logging. These credentials are intentionally managed through local environment variables and are not committed to GitHub.

The application is fully runnable locally using the setup instructions above. Without credentials, it still demonstrates the complete workflow through fallback AI report generation, local PDF creation, skipped email status handling, skipped Sheets logging, and the internal dashboard.

## Final Notes

This prototype focuses on a complete, practical automation workflow rather than isolated features.

It demonstrates:

* End-to-end workflow thinking
* Clean FastAPI structure
* Robust fallback handling
* Personalized report generation
* PDF creation
* Email automation readiness
* Optional Google Sheets bonus integration
* Clear status visibility through an admin dashboard

