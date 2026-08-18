"""Fixture containing hardcoded credentials security vulnerability."""

API_KEY_SECRET = "sk_live_1234567890abcdef"
DATABASE_PASSWORD = "super_secret_admin_password"


def connect_database() -> str:
    """Simulates database connection with hardcoded password."""
    return f"Connected with {DATABASE_PASSWORD}"
