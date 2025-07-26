"""
Main application file for the Unified OCR Service.

This file initializes the FastAPI application, configures middleware,
mounts static file directories, sets up HTML templates, and defines
the primary API and UI endpoints.
"""

# --- 1. Core Imports ---
import uuid
import structlog

# --- 2. Third-party Imports ---
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

# --- 3. Local Application Imports ---
from app.api.v1.endpoints import ocr as ocr_endpoint
from app.core.logging import configure_logging, correlation_id_var

# --- Application Initialization ---

# Configure structured logging at startup.
configure_logging()
logger = structlog.get_logger(__name__)

# Create the main FastAPI application instance.
app = FastAPI(
    title="Unified OCR Service",
    description="An integrated service for text detection, recognition, and document processing.",
    version="1.0.0"
)

# --- Middleware Configuration ---

# Best practice: For production, restrict origins to your specific frontend domain.
# Using ["*"] is suitable for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    """
    Inject a correlation ID into every incoming request for traceability.

    Checks for an 'X-Correlation-ID' header. If not found, a new UUID
    is generated. The ID is added to logs and the response headers.
    """
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_var.set(correlation_id)

    logger.info("request.started", method=request.method, url=str(request.url))
    response = await call_next(request)
    logger.info("request.finished", status_code=response.status_code)

    response.headers["X-Correlation-ID"] = correlation_id
    correlation_id_var.reset(token)
    return response


# --- Static Files and Templates ---

# Mount the 'static' directory to serve CSS, JS, and image files.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Point to the 'templates' directory for HTML files.
templates = Jinja2Templates(directory="templates")


# --- API Router Inclusion ---

# Include the OCR endpoint router with a versioned prefix.
app.include_router(ocr_endpoint.router, prefix="/v3", tags=["V3 - OCR"])


# --- UI and Health Check Endpoints ---

@app.get("/", response_class=HTMLResponse, tags=["User Interface"])
async def serve_frontend(request: Request):
    """
    Serve the main single-page application (SPA) user interface.

    Args:
        request: The incoming request object.

    Returns:
        An HTML response containing the rendered index.html.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Provide a simple health check endpoint to confirm the service is running.
    """
    logger.info("health_check.called", status="healthy")
    return {"status": "ok", "message": "OCR Service is running and healthy."}