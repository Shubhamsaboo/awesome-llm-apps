"""The `utils` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__)
