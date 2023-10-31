import bpy
from bpy.types import Context, Event, Operator, UILayout
from bpy.props import EnumProperty, StringProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn



class AP_OT_duplicate_active_layer(Operator):
    bl_idname = 'armature_picker.duplicate_active_layer'
    bl_label = 'Duplicate Active Layer'
    bl_description = "Make a duplicate of the active layer and all of its content"

    copy_layer_name: StringProperty(name="Copy Layer Name", default='Layer Copy')

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False, use_picker_editor=True, use_active_node=False)

    def invoke(self, context: Context, _event: Event) -> OpsReturn:
        self.copy_layer_name = context.space_data.node_tree.active_picker_layer.name + '.copy'
        return context.window_manager.invoke_props_dialog(self, width=320)

    def execute(self, context: Context) -> OpsReturn:
        from armature_picker.node_editor.node_tree import AP_NodeTree, refresh_nodes_cache
        picker: AP_NodeTree = context.space_data.node_tree
        widgets = picker.widgets_from_active_layer
        if len(widgets) == 0:
            return OpsReturn.CANCEL
        bpy.ops.node.select_all(False, action='DESELECT')
        for widget in widgets:
            widget.select = True
        picker.nodes.active = widgets[0]
        picker_layer_id = picker.new_layer(self.copy_layer_name).uuid
        bpy.ops.node.duplicate(False, keep_inputs=False) 
        # When copying node, it will get asigned the active layer ID...
        # for copy_node in context.selected_nodes:
        #     copy_node.picker_layer = picker_layer_id
        refresh_nodes_cache(picker)
        return OpsReturn.FINISH
