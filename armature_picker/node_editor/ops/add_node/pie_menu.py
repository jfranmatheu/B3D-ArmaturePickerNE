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
            if node is None:
                pie.separator()
                continue
            if isinstance(node, dict):
                menu_name = node['name']
                menu_icon = node['icon']
                items = node['items']
                col = pie.column(align=True)
                col.ui_units_x = 6.5
                header = col.box()
                header.scale_y = .9
                header.label(text=' '.join(menu_name)) #, icon=menu_icon)
                sub_pie = col.box().column(align=True)
                sub_pie.scale_y = 1.4
                sub_pie.emboss = 'PULLDOWN_MENU'
                for _node in items:
                    if isinstance(_node, tuple):
                        _node, label, icon = _node
                    else:
                        label = _node.bl_label
                        icon = _node.bl_icon
                    sub_pie.operator(AP_OT_add_node.bl_idname, text=label, icon=icon).node_idname = _node.bl_idname
            else:
                pie.operator(AP_OT_add_node.bl_idname, text=node.bl_label, icon=node.bl_icon).node_idname = node.bl_idname
