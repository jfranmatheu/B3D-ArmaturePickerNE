from bl_ui.space_node import NODE_PT_active_tool
from bl_ui.space_toolsystem_toolbar import NODE_PT_tools_active
from bl_ui.space_toolsystem_common import ToolActivePanelHelper, ToolSelectPanelHelper
from bpy.types import Context

from .override_cache import set_cls_attribute


@classmethod
def poll(cls, context: Context):
    if context.space_data.tree_type != 'AP_NODETREE':
        return cls.old_poll(context)
    return False


def draw(self, context):
    if context.space_data.type != 'NODE_EDITOR' or context.space_data.tree_type != 'AP_NODETREE':
        self.old_draw(context)


@staticmethod
def draw_active_tool_fallback(context, *args, **kwargs):
    if context.space_data.tree_type != 'AP_NODETREE':
        return ToolSelectPanelHelper.old_draw_active_tool_fallback(context, *args, **kwargs)

@classmethod
def tools_from_context(cls, context, mode=None):
    if context.space_data.tree_type != 'AP_NODETREE':
        yield cls.old_tools_from_context(context, mode=mode)
    yield None

def register():
    set_cls_attribute(NODE_PT_active_tool, 'poll', poll)
    # set_cls_attribute(NODE_PT_active_tool, '_tool_key_from_context', _tool_key_from_context)

    set_cls_attribute(NODE_PT_tools_active, 'poll', poll)
    # set_cls_attribute(NODE_PT_tools_active, 'draw_cls', draw_cls)
    # set_cls_attribute(NODE_PT_tools_active, 'tools_from_context', tools_from_context)
    
    set_cls_attribute(ToolActivePanelHelper, 'draw', draw)
    
    # set_cls_attribute(ToolSelectPanelHelper, 'draw_active_tool_fallback', draw_active_tool_fallback)
