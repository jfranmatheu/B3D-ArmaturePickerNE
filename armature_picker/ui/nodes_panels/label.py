from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from ..poll import poll_node
from ...node_editor.nodes.bone_picker.node import APNODE_BonePicker_StyleProps



class APNODE_PT_label(Panel):
    bl_idname = 'APNODE_PT_label'
    bl_label = 'Label'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'

    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_node(context)  and context.mode == 'EDIT_ARMATURE' and\
            isinstance(context.space_data.node_tree.nodes.active, APNODE_BonePicker_StyleProps)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section_style = draw_section(layout, 'Label', icon='FILE_TEXT')
        if node.use_image:
            section_style.enabled = False
        node.draw_label_props(section_style)
