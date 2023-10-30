from bpy.types import Context, Panel
try:
    from bpy.types import BoneCollection
    from bl_ui.properties_data_armature import DATA_PT_bone_collections
    from rna_prop_ui import draw as draw_rna_prop_ui
except ImportError as e:
    DATA_PT_bone_collections = None

from .ui_list import LIST_PickerLayers
from armature_picker.node_editor.poll import poll_check


class PickerLayersPanel(Panel):
    bl_idname = 'AP_PT_picker_layers'
    bl_label = "Picker Layers"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_order = 1

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False)


    def draw(self, context: Context):
        layout = self.layout

        node_tree = context.space_data.node_tree

        row = layout.row()

        row.template_list(
            LIST_PickerLayers.bl_idname, '',
            node_tree, 'picker_layers',
            node_tree, 'active_picker_layer_index',
            item_dyntip_propname='', rows=5, maxrows=5, type='DEFAULT'
        )

        actions = row.column(align=True)
        actions.operator('armature_picker.add_picker_layer', text='', icon='ADD')
        actions.operator('armature_picker.remove_picker_layer', text='', icon='REMOVE')
        actions.separator()
        actions.prop(node_tree, 'frame_layer_on_switch', text='', icon='LOCKVIEW_ON')


class BoneCollectionsPanel(Panel):
    bl_idname = 'AP_PT_bone_collections'
    bl_label = "Bone Collections"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_context = "data"
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
    bl_context = "data"
    bl_order = 1
    bl_parent_id = 'AP_PT_bone_collections'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=True) and DATA_PT_bone_collections is not None

    def draw(self, context: Context):
        draw_rna_prop_ui(self.layout, context, 'active_object.data.collections.active', BoneCollection)
