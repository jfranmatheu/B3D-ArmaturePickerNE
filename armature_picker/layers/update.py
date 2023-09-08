from bpy.types import NodeTree, Context

from ..node_editor.node_tree import AP_Node


def update_active_layer(node_tree: NodeTree, context: Context, active_layer_index: int) -> None:
    pass


def on_remove_layer(node_tree: NodeTree, context: Context, removed_layer_id: str) -> None:
    node: AP_Node
    for node in node_tree.nodes:
        if node.picker_layer == removed_layer_id:
            node.picker_layer = 'NONE'
