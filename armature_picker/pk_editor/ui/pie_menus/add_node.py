from bpy.types import Context, Menu, UILayout

from armature_picker.pk_editor.widgets import NODES
from armature_picker.pk_editor.ops.add_node import AP_OT_add_node


class MT_add_node(Menu):
    bl_idname = 'AP_MT_add_node'
    bl_label = "Add Widget"

    def draw_section(self, layout: UILayout, section_data: dict):
        menu_name = section_data['name']
        menu_icon = section_data['icon']
        items = section_data['items']
        # item_count = len(items)
        col = layout.column(align=True)
        col.ui_units_x = 6.5
        spacing = col.box()
        spacing.ui_units_y = 0.1
        spacing.scale_y = 1.45 * .9
        spacing.label(text=' ')
        header = col.box()
        header.scale_y = .9
        header.label(text=' '.join(menu_name)) #, icon=menu_icon)
        # spacing = col.box()
        # spacing.ui_units_y = 0.1
        # spacing.scale_y = 1.45 * item_count
        # spacing.label(text=' ')
        sub_pie = col.column(align=True) # col.box().column(align=True)
        sub_pie.scale_y = 1.4
        sub_pie.emboss = 'RADIAL_MENU'
        for _node in items:
            if isinstance(_node, tuple):
                _node, label, icon = _node
                if isinstance(_node, str):
                    node_idname = _node
                elif isinstance(_node, tuple):
                    node_idname = _node[0].bl_idname + '@' + _node[1] # Attached a preset function at pos 1 for node in pos 0.
                else:
                    node_idname = _node.bl_idname
            else:
                label = _node.bl_label
                icon = _node.bl_icon
                node_idname = _node.bl_idname
            sub_pie.operator(AP_OT_add_node.bl_idname, text=label, icon=icon).node_idname = node_idname

    def draw(self, context: Context):
        layout = self.layout
        pie = layout.menu_pie()
        # Pie order: west, east, south, north, north-west, north-east, south-west, south-east
        for node in NODES:
            if node is None:
                pie.separator()
                continue
            if isinstance(node, dict):
                self.draw_section(pie, node)
            elif isinstance(node, tuple):
                section_col = pie.column()
                for section in node:
                    self.draw_section(section_col, section)
                    section_col.separator()
            else:
                pie.operator(AP_OT_add_node.bl_idname, text=node.bl_label, icon=node.bl_icon).node_idname = node.bl_idname
