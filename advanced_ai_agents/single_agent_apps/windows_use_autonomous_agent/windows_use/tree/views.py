from dataclasses import dataclass,field

@dataclass
class TreeState:
    interactive_nodes:list['TreeElementNode']=field(default_factory=[])
    informative_nodes:list['TextElementNode']=field(default_factory=[])
    scrollable_nodes:list['ScrollElementNode']=field(default_factory=[])

    def interactive_elements_to_string(self)->str:
        return '\n'.join([f'Label: {index} App Name: {node.app_name} ControlType: {f'{node.control_type} Control'} Name: {node.name} Shortcut: {node.shortcut} Cordinates: {node.center.to_string()}' for index,node in enumerate(self.interactive_nodes)])
    
    def informative_elements_to_string(self)->str:
        return '\n'.join([f'App Name: {node.app_name} Name: {node.name}' for node in self.informative_nodes])
    
    def scrollable_elements_to_string(self)->str:
        n=len(self.interactive_nodes)
        return '\n'.join([f'Label: {n+index} App Name: {node.app_name} ControlType: {f'{node.control_type} Control'} Name: {node.name} Cordinates: {node.center.to_string()} Horizontal Scrollable: {node.horizontal_scrollable} Vertical Scrollable: {node.vertical_scrollable}' for index,node in enumerate(self.scrollable_nodes)])
    
@dataclass
class BoundingBox:
    left:int
    top:int
    right:int
    bottom:int

    def to_string(self):
        return f'({self.left},{self.top},{self.right},{self.bottom})'

@dataclass
class Center:
    x:int
    y:int

    def to_string(self)->str:
        return f'({self.x},{self.y})'

@dataclass
class TreeElementNode:
    name:str
    control_type:str
    shortcut:str
    bounding_box:BoundingBox
    center:Center
    app_name:str

@dataclass
class TextElementNode:
    name:str
    app_name:str

@dataclass
class ScrollElementNode:
    name:str
    control_type:str
    app_name:str
    center:Center
    horizontal_scrollable:bool
    vertical_scrollable:bool