"""WhyCode REST API package."""

from whycode.api.app import create_app
from whycode.api.routes import router

__all__ = ["create_app", "router"]
