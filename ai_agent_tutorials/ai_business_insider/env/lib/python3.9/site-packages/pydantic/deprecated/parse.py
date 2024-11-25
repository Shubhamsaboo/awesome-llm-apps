from __future__ import annotations

import json
import pickle
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from typing_extensions import deprecated

from ..warnings import PydanticDeprecatedSince20

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20


class Protocol(str, Enum):
    json = 'json'
    pickle = 'pickle'


@deprecated('`load_str_bytes` is deprecated.', category=None)
def load_str_bytes(
    b: str | bytes,
    *,
    content_type: str | None = None,
    encoding: str = 'utf8',
    proto: Protocol | None = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    warnings.warn('`load_str_bytes` is deprecated.', category=PydanticDeprecatedSince20, stacklevel=2)
    if proto is None and content_type:
        if content_type.endswith(('json', 'javascript')):
            pass
        elif allow_pickle and content_type.endswith('pickle'):
            proto = Protocol.pickle
        else:
            raise TypeError(f'Unknown content-type: {content_type}')

    proto = proto or Protocol.json

    if proto == Protocol.json:
        if isinstance(b, bytes):
            b = b.decode(encoding)
        return json_loads(b)  # type: ignore
    elif proto == Protocol.pickle:
        if not allow_pickle:
            raise RuntimeError('Trying to decode with pickle with allow_pickle=False')
        bb = b if isinstance(b, bytes) else b.encode()  # type: ignore
        return pickle.loads(bb)
    else:
        raise TypeError(f'Unknown protocol: {proto}')


@deprecated('`load_file` is deprecated.', category=None)
def load_file(
    path: str | Path,
    *,
    content_type: str | None = None,
    encoding: str = 'utf8',
    proto: Protocol | None = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    warnings.warn('`load_file` is deprecated.', category=PydanticDeprecatedSince20, stacklevel=2)
    path = Path(path)
    b = path.read_bytes()
    if content_type is None:
        if path.suffix in ('.js', '.json'):
            proto = Protocol.json
        elif path.suffix == '.pkl':
            proto = Protocol.pickle

    return load_str_bytes(
        b, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle, json_loads=json_loads
    )
