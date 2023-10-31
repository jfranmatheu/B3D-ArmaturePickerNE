import bpy
from bpy.types import Context, Event, Operator, NodeTree
from bpy.props import IntProperty, StringProperty

from armature_picker.node_editor.poll import poll_check
from ..utils.operator import OpsReturn
from ..utils.node_editor import deselect_all_nodes


class AddPickerLayer(Operator):
    bl_idname = 'armature_picker.add_picker_layer'
    bl_label = 'Add Picker Layer'

    layer_name: StringProperty(name="Layer Name", default='New Layer')

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context: Context) -> OpsReturn:
        context.space_data.node_tree.new_layer(name=self.layer_name)
        return OpsReturn.FINISH


class RemoveActivePickerLayer(Operator):
    bl_idname = 'armature_picker.remove_active_picker_layer'
    bl_label = 'W A R N I N G !\nAre you sure you want to remove ALL\nthe associated Widgets to this Layer?'
    bl_desctiption = "Remove Active Picker Layer (and all its associated widgets)\nIMPORTANT! This action can't be undone"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False) and len(context.space_data.node_tree.picker_layers) > 1

    def invoke(self, context: Context, event: Event):
        # self.widgets_to_remove = len(context.space_data.node_tree.widgets_from_active_layer)
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree

        if node_tree.active_picker_layer_index == -1:
            return OpsReturn.CANCEL

        if node_tree.active_picker_layer_index >= len(node_tree.picker_layers):
            return OpsReturn.CANCEL

        # Delete picker nodes from active picker layer.
        bpy.ops.node.select_all(False, action='DESELECT_ALL')
        widgets = self.widgets_from_active_layer
        if len(widgets) != 0:
            for widget in widgets:
                widget.select = True
            self.nodes.active = widgets[0]
            bpy.ops.node.delete(False)

        # Delete active picker layer from picker.
        self.picker_layers.remove(self.picker_layers.active_picker_layer_index)
        self.picker_layers.active_picker_layer_index = ( len(self.picker_layers) - 1 )
        return OpsReturn.FINISH
