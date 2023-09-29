from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section_h
from armature_picker.node_editor.poll import poll_check



class APNODE_PT_style(Panel):
    bl_idname = 'APNODE_PT_style'
    bl_label = 'Style'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'
    
    bl_order = 5

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=True)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        header, section_style = draw_section_h(layout, 'Style', icon='COLOR')
        if node.wg_type not in {'bone_picker_geo'}:
            header.prop(node, 'use_override_theme', text='Override Theme', icon='RESTRICT_COLOR_ON' if node.use_override_theme else 'RESTRICT_COLOR_OFF', toggle=True)
        node.draw_styles(layout, section_style)
