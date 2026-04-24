"""Compatibility entrypoint that re-exports the root FastAPI app."""

from main import app

__all__ = ["app"]
