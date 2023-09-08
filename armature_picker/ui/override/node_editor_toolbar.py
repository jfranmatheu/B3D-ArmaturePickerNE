from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
from bpy.types import Context, UILayout

from .override_cache import set_cls_attribute


@classmethod
def draw_cls(cls, layout: UILayout, context: Context, detect_layout=True, scale_y=1.75):
    if context.space_data.type != 'NODE_EDITOR' or context.space_data.tree_type != 'AP_NODETREE':
        cls.old_draw_cls(layout, context, detect_layout, scale_y)
        return


def register():
    set_cls_attribute(ToolSelectPanelHelper, 'draw_cls', draw_cls)
