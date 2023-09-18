from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from armature_picker.node_editor.poll import poll_check
from ...node_editor.nodes.bone_picker_geo.node import APNODE_BonePickerGeo



class APNODE_PT_source_mesh_object(Panel):
    bl_idname = 'APNODE_PT_source_mesh_object'
    bl_label = 'Object'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'

    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=APNODE_BonePickerGeo)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section_style = draw_section(layout, 'Source Mesh Object', icon='MESH_DATA')
        node.draw_object_props(section_style)
