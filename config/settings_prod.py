from .settings import *

DEBUG = False

ALLOWED_HOSTS = ["parkinsons-digest-055d912d3991.herokuapp.com"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
