from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
from bpy.types import Context, UILayout

from .override_cache import set_cls_attribute, get_attr_from_cache
from armature_picker.pk_editor.poll import poll_check


@classmethod
def draw_cls(cls, layout: UILayout, context: Context, detect_layout=True, scale_y=1.75):
    if context.space_data.type != 'NODE_EDITOR' or context.space_data.tree_type != 'AP_NODETREE':
        cls.old_draw_cls(layout, context, detect_layout, scale_y)
        return
    
    if poll_check(context, 'POSE', use_active_object=True, use_picker_editor=True, use_view3d=True):
        toolbar = layout.column(align=True)
        toolbar.scale_x = 2.0
        toolbar.scale_y = 2.0
        toolbar.prop(context.window_manager.armature_picker, 'active_tool', expand=True, icon_only=True)


def register():
    set_cls_attribute(ToolSelectPanelHelper, 'draw_cls', draw_cls)
