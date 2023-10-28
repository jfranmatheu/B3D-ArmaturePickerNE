from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from armature_picker.node_editor.poll import poll_check
from ...node_editor.nodes.bone_picker.node import AP_BonePickerNode
from ...node_editor.nodes._button_common import APNODE_Button_Common



class APNODE_PT_button(Panel):
    bl_idname = 'APNODE_PT_button'
    bl_label = 'Button'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'

    bl_order = 2

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=APNODE_Button_Common)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active
        node.draw_button_props(context, layout)
