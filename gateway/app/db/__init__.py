"""Persistence layer (Neon/Postgres) with in-memory fallback for dev/tests.

Repositories are accessed behind protocols so handlers don't care whether
they're talking to Postgres or an in-memory dict. All DB access is off the
gateway's hot request path (auth at login, history via a background sink).
"""
