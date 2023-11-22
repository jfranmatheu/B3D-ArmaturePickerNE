from bpy.types import Context, Panel

from armature_picker.utils.ui_layout import draw_section
from armature_picker.pk_editor.poll import poll_check
from armature_picker.pk_editor.widgets._slider_common import APNODE_Slider_CommonNode


class APNODE_PT_widget_properties(Panel):
    bl_idname = 'APNODE_PT_widget_properties'
    bl_label = 'Widget Properties'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'

    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=True, use_picker_editor=True)

    def draw(self, context: Context):
        context.space_data.node_tree.nodes.active.draw_wg_props(context, self.layout)
