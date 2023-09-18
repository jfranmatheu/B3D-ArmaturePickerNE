from bpy.types import Context, Panel

from .ui_list import LIST_PickerLayers
from armature_picker.node_editor.poll import poll_check


class PickerLayersPanel(Panel):
    bl_idname = 'AP_PT_picker_layers'
    bl_label = "Picker Layers"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

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
            node_tree, 'active_picker_layer',
            item_dyntip_propname='', rows=5, maxrows=5, type='DEFAULT'
        )
        
        actions = row.column(align=True)
        actions.operator('armature_picker.add_picker_layer', text='', icon='ADD')
        actions.operator('armature_picker.remove_picker_layer', text='', icon='REMOVE')
