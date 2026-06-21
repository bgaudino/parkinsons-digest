from .settings import *  # noqa: F401,F403

# Local overrides. Copy to settings_local.py (gitignored) and set
# DJANGO_SETTINGS_MODULE=config.settings_local in your .env to use it.

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
