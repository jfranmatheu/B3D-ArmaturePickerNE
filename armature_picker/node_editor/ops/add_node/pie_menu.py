from bpy.types import Context, Menu

from ...nodes import NODES
from .op import AP_OT_add_node


class MT_add_node(Menu):
    bl_idname = 'AP_MT_add_node'
    bl_label = "Add Node"
    
    def draw(self, context: Context):
        layout = self.layout
        pie = layout.menu_pie()
        # Pie order: west, east, south, north, north-west, north-east, south-west, south-east
        for node in NODES:
            pie.operator(AP_OT_add_node.bl_idname, text=node.bl_label, icon=node.bl_icon).node_idname = node.bl_idname
