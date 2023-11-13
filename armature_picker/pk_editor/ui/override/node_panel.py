from bl_ui.space_node import NODE_PT_active_node_generic, NODE_PT_active_node_color
# from bl_ui.properties_grease_pencil_common import AnnotationDataPanel
from bpy.types import Context, NODE_PT_annotation, NODE_PT_active_node_properties

from .override_cache import set_cls_attribute


@classmethod
def poll(cls, context: Context) -> bool:
    if context.area.type == 'NODE_EDITOR':
        return context.space_data.tree_type != 'AP_NODETREE'
    return True


def register():
    set_cls_attribute(NODE_PT_active_node_generic, 'poll', poll)
    set_cls_attribute(NODE_PT_active_node_properties, 'poll', poll)
    set_cls_attribute(NODE_PT_annotation, 'poll', poll)
