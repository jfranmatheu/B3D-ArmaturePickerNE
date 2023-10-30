from bpy.types import Context, Event, Operator, NodeTree
from bpy.props import IntProperty

from uuid import uuid4

from armature_picker.node_editor.poll import poll_check
from ..utils.operator import OpsReturn
from ..utils.node_editor import deselect_all_nodes


class AddPickerLayer(Operator):
    bl_idname = 'armature_picker.add_picker_layer'
    bl_label = 'Add Picker Layer'

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False)

    def execute(self, context: Context) -> OpsReturn:
        context.space_data.node_tree.new_layer(name='New Layer')
        return OpsReturn.FINISH


class RemovePickerLayer(Operator):
    bl_idname = 'armature_picker.remove_picker_layer'
    bl_label = 'W A R N I N G !\nAre you sure you want to remove ALL\nthe associated Widgets to this Layer?'
    bl_desctiption = "Remove Active Picker Layer (and all its associated widgets)\nIMPORTANT! This action can't be undone"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False) and len(context.space_data.node_tree.picker_layers) > 1

    def invoke(self, context: Context, event: Event):
        self.widgets_to_remove = len(context.space_data.node_tree.widgets_from_active_layer)
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree

        if node_tree.active_picker_layer_index == -1:
            return OpsReturn.CANCEL

        if node_tree.active_picker_layer_index >= len(node_tree.picker_layers):
            return OpsReturn.CANCEL

        node_tree.remove_layer(uuid_or_index=node_tree.active_picker_layer_index)
        return OpsReturn.FINISH



class SelectNodesInPickerLayer(Operator):
    bl_idname = 'armature_picker.select_nodes_in_picker_layer'
    bl_label = 'Select Nodes in Picker Layer'

    picker_layer_index: IntProperty(default=-1)

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree
        picker_layer_id: str = node_tree.picker_layers[self.picker_layer_index].uuid
        for node in node_tree.nodes:
            node.select = picker_layer_id == node.picker_layer

        if context.selected_nodes != []:
            node_tree.nodes.active = context.selected_nodes[0]

        return OpsReturn.FINISH
