from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import create_db_and_tables
from app.routers import leads


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered lead intake, company enrichment, PDF audit generation, and email automation prototype.",
    version="1.0.0",
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates


@app.on_event("startup")
def on_startup() -> None:
    """
    Initialize database tables when the app starts.
    """
    create_db_and_tables()


app.include_router(leads.router)


@app.get("/")
def root():
    """
    Redirect-style API message for the project root.
    The actual form is available at /leads/form.
    """
    return {
        "message": "SimplifiQ Lead Automation API is running",
        "status": "ok",
        "lead_form": "/leads/form",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint useful for deployment platforms.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }
    )