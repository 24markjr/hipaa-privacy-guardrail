"""Middleware stack. Every request flows through these — routers stay thin.

Outermost → innermost order (configured in app/main.py):

    RequestContextMiddleware   # assign request_id + trace_id, expose via contextvars
        └─ AccessLogMiddleware # structured JSON access log + timing
            └─ AuthMiddleware  # reject unauthenticated before any real work
                └─ routers
"""
