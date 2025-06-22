from windows_use.tree.views import TreeElementNode, TextElementNode, ScrollElementNode, Center, BoundingBox, TreeState
from windows_use.tree.config import INTERACTIVE_CONTROL_TYPE_NAMES,INFORMATIVE_CONTROL_TYPE_NAMES
from concurrent.futures import ThreadPoolExecutor, as_completed
from uiautomation import GetRootControl,Control,ImageControl
from windows_use.desktop.config import AVOIDED_APPS
from PIL import Image, ImageFont, ImageDraw
from typing import TYPE_CHECKING
from time import sleep
import random

if TYPE_CHECKING:
    from windows_use.desktop import Desktop

class Tree:
    def __init__(self,desktop:'Desktop'):
        self.desktop=desktop

    def get_state(self)->TreeState:
        sleep(0.15)
        # Get the root control of the desktop
        root=GetRootControl()
        interactive_nodes,informative_nodes,scrollable_nodes=self.get_appwise_nodes(node=root)
        return TreeState(interactive_nodes=interactive_nodes,informative_nodes=informative_nodes,scrollable_nodes=scrollable_nodes)
    
    def get_appwise_nodes(self,node:Control) -> tuple[list[TreeElementNode],list[TextElementNode]]:
        all_apps=node.GetChildren()
        visible_apps = {app.Name: app for app in all_apps if self.desktop.is_app_visible(app) and app.Name not in AVOIDED_APPS}
        apps={'Taskbar':visible_apps.pop('Taskbar'),'Program Manager':visible_apps.pop('Program Manager')}
        if visible_apps:
            foreground_app = list(visible_apps.values()).pop(0)
            apps[foreground_app.Name.strip()]=foreground_app
        interactive_nodes,informative_nodes,scrollable_nodes=[],[],[]
        # Parallel traversal (using ThreadPoolExecutor) to get nodes from each app
        with ThreadPoolExecutor() as executor:
            future_to_node = {executor.submit(self.get_nodes, app): app for app in apps.values()}
            for future in as_completed(future_to_node):
                try:
                    result = future.result()
                    if result:
                        element_nodes,text_nodes,scroll_nodes=result
                        interactive_nodes.extend(element_nodes)
                        informative_nodes.extend(text_nodes)
                        scrollable_nodes.extend(scroll_nodes)
                except Exception as e:
                    print(f"Error processing node {future_to_node[future].Name}: {e}")
        return interactive_nodes,informative_nodes,scrollable_nodes

    def get_nodes(self, node: Control) -> tuple[list[TreeElementNode],list[TextElementNode],list[ScrollElementNode]]:
        interactive_nodes, informative_nodes, scrollable_nodes = [], [], []
        app_name=node.Name.strip()
        app_name='Desktop' if app_name=='Program Manager' else app_name
        def is_element_interactive(node:Control):
            try:
                if node.ControlTypeName in INTERACTIVE_CONTROL_TYPE_NAMES:
                    if is_element_visible(node) and is_element_enabled(node) and not is_element_image(node):
                        return True
            except Exception as ex:
                return False
            return False
        
        def is_element_visible(node:Control,threshold:int=0):
            box=node.BoundingRectangle
            if box.isempty():
                return False
            width=box.width()
            height=box.height()
            area=width*height
            is_offscreen=not node.IsOffscreen
            return area > threshold and is_offscreen
    
        def is_element_enabled(node:Control):
            try:
                return node.IsEnabled
            except Exception as ex:
                return False
        
        def is_element_image(node:Control):
            if isinstance(node,ImageControl):
                if not node.Name.strip() or node.LocalizedControlType=='graphic':
                    return True
            return False
        
        def is_element_text(node:Control):
            try:
                if node.ControlTypeName in INFORMATIVE_CONTROL_TYPE_NAMES:
                    if is_element_visible(node) and is_element_enabled(node) and not is_element_image(node):
                        return True
            except Exception as ex:
                return False
            return False
        
        def is_element_scrollable(node:Control):
            try:
                scroll_pattern=node.GetScrollPattern()
                return scroll_pattern.VerticallyScrollable or scroll_pattern.HorizontallyScrollable
            except Exception as ex:
                return False
            
        def tree_traversal(node: Control):
            if is_element_interactive(node):
                box = node.BoundingRectangle
                x,y=box.xcenter(),box.ycenter()
                center = Center(x=x,y=y)
                interactive_nodes.append(TreeElementNode(
                    name=node.Name.strip() or "''",
                    control_type=node.LocalizedControlType.title(),
                    shortcut=node.AcceleratorKey or "''",
                    bounding_box=BoundingBox(left=box.left,top=box.top,right=box.right,bottom=box.bottom),
                    center=center,
                    app_name=app_name
                ))
            elif is_element_text(node):
                informative_nodes.append(TextElementNode(
                    name=node.Name.strip() or "''",
                    app_name=app_name
                ))
            elif is_element_scrollable(node):
                scroll_pattern=node.GetScrollPattern()
                box = node.BoundingRectangle
                x,y=box.xcenter(),box.ycenter()
                center = Center(x=x,y=y)
                scrollable_nodes.append(ScrollElementNode(
                    name=node.Name.strip() or node.LocalizedControlType.capitalize() or "''",
                    app_name=app_name,
                    control_type=node.LocalizedControlType.title(),
                    center=center,
                    horizontal_scrollable=scroll_pattern.HorizontallyScrollable,
                    vertical_scrollable=scroll_pattern.VerticallyScrollable
                ))
                
            # Recursively check all children
            for child in node.GetChildren():
                tree_traversal(child)
        tree_traversal(node)
        return (interactive_nodes,informative_nodes,scrollable_nodes)
    
    def get_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def annotate(self,nodes:list[TreeElementNode])->Image:
        screenshot=self.desktop.get_screenshot()
        # Include padding to the screenshot
        padding=20
        width=screenshot.width+(2*padding)
        height=screenshot.height+(2*padding)
        padded_screenshot=Image.new("RGB", (width, height), color=(255, 255, 255))
        padded_screenshot.paste(screenshot, (padding,padding))
        # Create a layout above the screenshot to place bounding boxes.
        draw=ImageDraw.Draw(padded_screenshot)
        font_size=12
        try:
            font=ImageFont.truetype('arial.ttf',font_size)
        except:
            font=ImageFont.load_default()
        for label,node in enumerate(nodes):
            box=node.bounding_box
            color=self.get_random_color()
            # Adjust bounding box to fit padded image
            adjusted_box = (
                box.left + padding, box.top + padding,  # Adjust top-left corner
                box.right + padding, box.bottom + padding  # Adjust bottom-right corner
            )
            # Draw bounding box around the element in the screenshot
            draw.rectangle(adjusted_box,outline=color,width=2)
            
            # Get the size of the label
            label_width=draw.textlength(str(label),font=font,font_size=font_size)
            label_height=font_size
            left,top,right,bottom=adjusted_box
            # Position the label above the bounding box and towards the right
            label_x1 = right - label_width  # Align the right side of the label with the right edge of the box
            label_y1 = top - label_height - 4  # Place the label just above the top of the bounding box, with some padding

            # Draw the label background rectangle
            label_x2 = label_x1 + label_width
            label_y2 = label_y1 + label_height + 4  # Add some padding

            # Draw the label background rectangle
            draw.rectangle([(label_x1, label_y1), (label_x2, label_y2)], fill=color)

            # Draw the label text
            text_x = label_x1 + 2  # Padding for text inside the rectangle
            text_y = label_y1 + 2
            draw.text((text_x, text_y), str(label), fill=(255, 255, 255), font=font)
        return padded_screenshot