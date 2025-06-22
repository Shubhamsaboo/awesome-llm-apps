from typing import Set

AVOIDED_APPS:Set[str]=set([
    'Recording toolbar'
])

EXCLUDED_APPS:Set[str]=set([
    'Program Manager','Taskbar'
]).union(AVOIDED_APPS)