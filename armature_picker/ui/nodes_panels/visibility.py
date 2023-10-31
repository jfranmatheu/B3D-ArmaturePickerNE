'''
from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from armature_picker.node_editor.poll import poll_check



class APNODE_PT_visibility(Panel):
    bl_idname = 'APNODE_PT_visibility'
    bl_label = 'Visibility'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'
    
    bl_options = {'HIDE_HEADER'}

    bl_order = 0

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=True)

    def draw(self, context: Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True
        node = context.space_data.node_tree.nodes.active

        # section_v = draw_section(layout, 'Visibility', icon='HIDE_OFF')
        node.draw_visibility(layout)
'''
