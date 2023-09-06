from bl_ui.space_node import NODE_PT_active_node_generic, NODE_PT_active_node_color
from bpy.types import Context

from .override_cache import set_cls_attribute


@classmethod
def poll(cls, context: Context):
    return context.space_data.tree_type != 'AP_NODETREE'


def register():
    set_cls_attribute(NODE_PT_active_node_generic, 'poll', poll)
