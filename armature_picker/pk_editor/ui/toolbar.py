from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
from bpy.types import Context, UILayout

from armature_picker.pk_editor.poll import poll_check
from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_tree_type



@ACK.Deco.UI_OVERRIDE(ToolSelectPanelHelper, 'draw', poll=poll_tree_type)
def draw_picker_editor_toolbar(self, context: Context) -> None:
    if poll_check(context, 'POSE', use_active_object=True, use_picker_editor=True, use_view3d=True):
        layout = self.layout
        toolbar = layout.column(align=True)
        toolbar.scale_x = 2.0
        toolbar.scale_y = 2.0
        toolbar.prop(context.window_manager.armature_picker, 'active_tool', expand=True, icon_only=True)
