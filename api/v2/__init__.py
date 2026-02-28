# API v2 - D1 Storage Version
from .routes_d1 import router as v2_router
from .routes_daily import router as daily_router

__all__ = ['v2_router', 'daily_router']
