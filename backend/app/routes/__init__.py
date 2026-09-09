from app.routes.cases import router as cases_router
from app.routes.health import router as health_router
from app.routes.audit import router as audit_router
from app.routes.screening import router as screening_router
from app.routes.documents import router as documents_router
from app.routes.dashboard import router as dashboard_router
from app.routes.model import router as model_router

__all__ = [
    "cases_router",
    "health_router",
    "audit_router",
    "screening_router",
    "documents_router",
    "dashboard_router",
    "model_router",
]
