from bpy.types import Context, Operator, NodeTree

from uuid import uuid4

from .poll import poll_node_editor
from ..utils.operator import OpsReturn
from .update import on_remove_layer


class AddPickerLayer(Operator):
    bl_idname = 'armature_picker.add_picker_layer'
    bl_label = 'Add Picker Layer'

    @classmethod
    def poll(cls, context: Context):
        return poll_node_editor(context)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree

        node_tree.active_picker_layer = len(node_tree.picker_layers)
        new_picker_layer = node_tree.picker_layers.add()
        new_picker_layer.name = uuid4().hex

        return OpsReturn.FINISH


class RemovePickerLayer(Operator):
    bl_idname = 'armature_picker.remove_picker_layer'
    bl_label = 'Remove Active Picker Layer'

    @classmethod
    def poll(cls, context: Context):
        return poll_node_editor(context)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree

        if node_tree.active_picker_layer == -1:
            return OpsReturn.CANCEL

        if node_tree.active_picker_layer >= len(node_tree.picker_layers):
            return OpsReturn.CANCEL

        node_tree.picker_layers.remove(node_tree.active_picker_layer) # node_tree.picker_layers[node_tree.active_picker_layer])

        on_remove_layer(node_tree, context, node_tree.active_picker_layer)

        node_tree.active_picker_layer = ( len(node_tree.picker_layers) - 1 )

        return OpsReturn.FINISH
