from bpy.types import Context, Panel

from armature_picker.ops import Ops as AP_OPS
from armature_picker.utils.ui_layout import draw_section
from armature_picker.pk_editor.poll import poll_check
from armature_picker.pk_editor.widgets.bone_picker_geo.node import APNODE_BonePickerGeo


class APNODE_PT_custom_shape(Panel):
    bl_idname = 'APNODE_PT_custom_shape'
    bl_label = 'Custom Shape'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'

    bl_order = 2

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=APNODE_BonePickerGeo)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section = draw_section(layout, 'Load Shape', icon='MONKEY')
        section.scale_y = 1.4
        AP_OPS.LoadCustomShapeFromGeometry.draw_in_layout(section, label='From Geometry', icon='MESH_DATA')

        section = draw_section(layout, 'Hitbox Settings', icon='STYLUS_PRESSURE')
        section.use_property_split = True
        section.column().prop(node, 'geo_precision', text='Precision', expand=True)
