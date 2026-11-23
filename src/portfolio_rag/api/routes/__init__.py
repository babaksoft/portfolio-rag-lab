"""FastAPI route modules."""

from portfolio_rag.api.routes.auth import router as auth_router
from portfolio_rag.api.routes.health import router as health_router
from portfolio_rag.api.routes.messages import router as messages_router

__all__ = ["auth_router", "health_router", "messages_router"]
