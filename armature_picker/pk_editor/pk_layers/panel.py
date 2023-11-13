from bpy.types import Context, Panel
try:
    from bpy.types import BoneCollection
    from bl_ui.properties_data_armature import DATA_PT_bone_collections
    from rna_prop_ui import draw as draw_rna_prop_ui
except ImportError as e:
    DATA_PT_bone_collections = None

from .ui_list import LIST_PickerLayers
from armature_picker.pk_editor.poll import poll_check


class PickerLayersPanel(Panel):
    bl_idname = 'AP_PT_picker_layers'
    bl_label = "Picker Layers"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Picker'
    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=True) and context.space_data.node_tree.library is None

    def draw(self, context: Context):
        layout = self.layout

        node_tree = context.space_data.node_tree

        row = layout.row()

        row.template_list(
            LIST_PickerLayers.bl_idname, '',
            node_tree, 'pk_layers',
            node_tree, 'active_picker_layer_index',
            item_dyntip_propname='', rows=5, maxrows=5, type='DEFAULT'
        )

        actions = row.column(align=True)
        actions.operator('armature_picker.add_picker_layer', text='', icon='ADD')
        actions.operator('armature_picker.remove_active_picker_layer', text='', icon='REMOVE')
        actions.separator()
        actions.operator('armature_picker.duplicate_active_layer', text='', icon='DUPLICATE')
        actions.separator()
        actions.prop(node_tree, 'use_preserve_picker_layer_view', text='', icon='LOCKVIEW_ON' if node_tree.use_preserve_picker_layer_view else 'LOCKVIEW_OFF')


class BoneCollectionsPanel(Panel):
    bl_idname = 'AP_PT_bone_collections'
    bl_label = "Bone Collections"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_context = "child"
    bl_order = 2

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=True) and DATA_PT_bone_collections is not None

    def draw(self, context: Context):
        self.armature = context.active_object.data
        DATA_PT_bone_collections.draw(self, self)


class BoneCollectionCustomPropertiesPanel(Panel):
    bl_idname = 'AP_PT_bone_collection_custom_properties'
    bl_label = "Custom Properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_context = "child"
    bl_order = 1
    bl_parent_id = 'AP_PT_bone_collections'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=True) and DATA_PT_bone_collections is not None

    def draw(self, context: Context):
        draw_rna_prop_ui(self.layout, context, 'active_object.child.collections.active', BoneCollection)
