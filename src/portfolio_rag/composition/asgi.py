"""Composed ASGI entry point for Uvicorn."""

from portfolio_rag.composition.api import create_app

app = create_app()
