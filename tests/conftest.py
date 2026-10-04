"""
Suite-wide test configuration.

Environment variables are set before any application module is imported so the tests
never depend on (or spend) the developer's local .env: no real provider keys, and the
pre-authentication API tests run with authentication switched off. Tests that exercise
authentication turn it on explicitly.
"""

import os

# A test that forgets to override the session must not reach the developer's real database
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["STUDIO_AUTO_RESUME"] = "false"
# Never launch the real Antigravity CLI (and spend its quota) from a test
os.environ["STUDIO_ENGINE"] = "loop"
os.environ["STUDIO_DEVELOPERS"] = "2"
os.environ["AUTH_REQUIRED"] = "false"
os.environ["AUTH_SECRET_KEY"] = "test-signing-secret-not-for-production-use"
os.environ["ADMIN_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GROQ_MODEL"] = "llama-3.3-70b-versatile"
os.environ["OPENAI_API_KEY"] = ""
