from bl_ui.space_node import NODE_PT_active_tool
from bl_ui.space_toolsystem_toolbar import NODE_PT_tools_active
from bl_ui.space_toolsystem_common import ToolActivePanelHelper, ToolSelectPanelHelper

from armature_picker.ackit._register.override_cache import set_cls_attribute
from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_picker_editor


def draw(self, context):
    if not poll_picker_editor(context):
        self.old_draw(context)


def register():
    ACK.Helper.UI_HIDE(NODE_PT_active_tool, poll_picker_editor)
    ACK.Helper.UI_HIDE(NODE_PT_tools_active, poll_picker_editor)
    ACK.Helper.UI_HIDE(ToolActivePanelHelper, poll_picker_editor)

    set_cls_attribute(ToolActivePanelHelper, 'draw', draw)
