from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("remotejwt")
except PackageNotFoundError:
    # package is not installed
    __version__ = None
