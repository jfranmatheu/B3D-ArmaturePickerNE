from bpy.types import Context


def poll_pose(context: Context) -> bool:
    return context.mode == 'POSE'

def poll_active_object(context: Context) -> bool:
    return context.active_object is not None and context.active_object.type in {'ARMATURE'}

def poll_node_editor(context: Context) -> bool:
    return context.area.type == 'NODE_EDITOR' and context.space_data.tree_type == 'AP_NODETREE' and context.space_data.node_tree is not None

def poll_node_editor__edit(context: Context) -> bool:
    return poll_node_editor(context) and context.space_data.node_tree.picker_mode == 'EDIT'

def poll_node_editor__pose(context: Context) -> bool:
    return poll_node_editor(context) and context.space_data.node_tree.picker_mode == 'POSE'

def poll_node(context: Context) -> bool:
    return context.space_data.node_tree.nodes.active is not None


def poll_check(context: Context,
               picker_mode: str = 'ANY',
               use_active_object: bool = True,
               use_picker_editor: bool = True,
               use_active_node: bool = False,
               use_view3d: bool = False) -> bool:
    if use_active_object:
        if not poll_pose(context):
            return False
        if not poll_active_object(context):
            return False
    if use_picker_editor:
        if not poll_node_editor(context):
            return False
        node_tree = context.space_data.node_tree
        if picker_mode != 'ANY' and picker_mode != node_tree.picker_mode:
            return False
        if use_active_node != False:
            if not poll_node(context):
                return False
            if not isinstance(use_active_node, bool) and not isinstance(node_tree.nodes.active, use_active_node):
                return False
    if use_view3d:
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                return True
        return False
    return True
