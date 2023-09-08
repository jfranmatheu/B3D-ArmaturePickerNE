from bpy.types import Context


def poll_node_editor(context: Context) -> bool:
    return context.space_data.tree_type == 'AP_NODETREE' and context.space_data.node_tree is not None
