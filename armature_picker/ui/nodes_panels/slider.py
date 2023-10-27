from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from armature_picker.node_editor.poll import poll_check
from ...node_editor.nodes._slider_common import APNODE_Slider_CommonNode



class APNODE_PT_slider_contraints(Panel):
    bl_idname = 'APNODE_PT_slider_contraints'
    bl_label = 'Slider'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'

    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=APNODE_Slider_CommonNode)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section_style = draw_section(layout, 'Slider Constraints', icon='MESH_DATA')
        node.draw_slider_constraints_props(section_style)
