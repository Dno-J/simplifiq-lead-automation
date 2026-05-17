import os
from datetime import datetime, timezone
from typing import Any, Dict

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def sheets_is_configured() -> bool:
    """
    Check whether Google Sheets logging is enabled and configured.

    The service account file must exist locally, and the target sheet ID must
    be present in environment variables.
    """
    return all(
        [
            settings.GOOGLE_SHEETS_ENABLED,
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            os.path.exists(settings.GOOGLE_SERVICE_ACCOUNT_FILE),
            settings.GOOGLE_SHEET_ID,
            settings.GOOGLE_SHEET_RANGE,
        ]
    )


def append_lead_to_sheet(lead_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Append a processed lead row to Google Sheets.

    Expected columns:
    Timestamp, Name, Email, Company, Website, Report Status, Email Status
    """

    if not sheets_is_configured():
        return {
            "status": "skipped",
            "error": "Google Sheets logging is disabled or not configured.",
        }

    try:
        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )

        service = build("sheets", "v4", credentials=credentials)

        values = [
            [
                datetime.now(timezone.utc).isoformat(),
                lead_data.get("full_name", ""),
                lead_data.get("email", ""),
                lead_data.get("company_name", ""),
                lead_data.get("company_website", ""),
                lead_data.get("report_status", ""),
                lead_data.get("email_status", ""),
            ]
        ]

        body = {
            "values": values,
        }

        service.spreadsheets().values().append(
            spreadsheetId=settings.GOOGLE_SHEET_ID,
            range=settings.GOOGLE_SHEET_RANGE,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

        return {
            "status": "logged",
            "error": "",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }