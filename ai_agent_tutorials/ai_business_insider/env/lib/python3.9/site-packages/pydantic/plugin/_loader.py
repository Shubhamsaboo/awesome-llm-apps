from __future__ import annotations

import importlib.metadata as importlib_metadata
import os
import warnings
from typing import TYPE_CHECKING, Final, Iterable

if TYPE_CHECKING:
    from . import PydanticPluginProtocol


PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'

# cache of plugins
_plugins: dict[str, PydanticPluginProtocol] | None = None
# return no plugins while loading plugins to avoid recursion and errors while import plugins
# this means that if plugins use pydantic
_loading_plugins: bool = False


def get_plugins() -> Iterable[PydanticPluginProtocol]:
    """Load plugins for Pydantic.

    Inspired by: https://github.com/pytest-dev/pluggy/blob/1.3.0/src/pluggy/_manager.py#L376-L402
    """
    disabled_plugins = os.getenv('PYDANTIC_DISABLE_PLUGINS')
    global _plugins, _loading_plugins
    if _loading_plugins:
        # this happens when plugins themselves use pydantic, we return no plugins
        return ()
    elif disabled_plugins in ('__all__', '1', 'true'):
        return ()
    elif _plugins is None:
        _plugins = {}
        # set _loading_plugins so any plugins that use pydantic don't themselves use plugins
        _loading_plugins = True
        try:
            for dist in importlib_metadata.distributions():
                for entry_point in dist.entry_points:
                    if entry_point.group != PYDANTIC_ENTRY_POINT_GROUP:
                        continue
                    if entry_point.value in _plugins:
                        continue
                    if disabled_plugins is not None and entry_point.name in disabled_plugins.split(','):
                        continue
                    try:
                        _plugins[entry_point.value] = entry_point.load()
                    except (ImportError, AttributeError) as e:
                        warnings.warn(
                            f'{e.__class__.__name__} while loading the `{entry_point.name}` Pydantic plugin, '
                            f'this plugin will not be installed.\n\n{e!r}'
                        )
        finally:
            _loading_plugins = False

    return _plugins.values()
