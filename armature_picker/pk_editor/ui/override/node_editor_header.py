from bl_ui.space_node import NODE_HT_header
from bpy.types import Context

from .override_cache import set_cls_attribute
from .. import header


def draw(self, context: Context):
    if context.space_data.tree_type != 'AP_NODETREE':
        self.old_draw(context)
        return

    header.draw_picker_editor_header(self, context)


def register():
    set_cls_attribute(NODE_HT_header, 'draw', draw)
