from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("django-easyjwt")
except PackageNotFoundError:
    __version__ = "0.7.6"  # Fallback for development

__all__ = ["__version__"]
