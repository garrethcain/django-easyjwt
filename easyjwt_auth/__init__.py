from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("easyjwt_auth")
except PackageNotFoundError:
    # package is not installed
    __version__ = None
