from django.core.exceptions import ImproperlyConfigured


class InvalidTaskBackend(ImproperlyConfigured):
    """Invalid task alias or backend configuration."""
