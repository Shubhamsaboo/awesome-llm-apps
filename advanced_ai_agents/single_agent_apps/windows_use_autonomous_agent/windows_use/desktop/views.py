from windows_use.tree.views import TreeState
from dataclasses import dataclass
from typing import Literal,Optional

@dataclass
class App:
    name:str
    depth:int
    status:Literal['Maximized','Minimized','Normal']
    size:'Size'

    def to_string(self):
        return f'Name: {self.name}|Depth: {self.depth}|Status: {self.status}|Size: {self.size.to_string()}'

@dataclass
class Size:
    width:int
    height:int

    def to_string(self):
        return f'({self.width},{self.height})'

@dataclass
class DesktopState:
    apps:list[App]
    active_app:Optional[App]
    screenshot:bytes|None
    tree_state:TreeState

    def active_app_to_string(self):
        if self.active_app is None:
            return 'No active app'
        return self.active_app.to_string()

    def apps_to_string(self):
        if len(self.apps)==0:
            return 'No apps opened'
        return '\n'.join([app.to_string() for app in self.apps])