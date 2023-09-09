from bl_ui.space_node import NODE_PT_node_tree_interface_inputs, NODE_PT_node_tree_interface_outputs
from bpy.types import Context

from .override_cache import set_cls_attribute


@classmethod
def poll(cls, context: Context):
    if context.space_data.tree_type != 'AP_NODETREE':
        return cls.old_poll(context)
    return False


def register():
    set_cls_attribute(NODE_PT_node_tree_interface_inputs, 'poll', poll)
    set_cls_attribute(NODE_PT_node_tree_interface_outputs, 'poll', poll)
