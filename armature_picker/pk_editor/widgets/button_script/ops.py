import bpy
from bpy.types import Context, Operator, Text, SpaceTextEditor

from ...poll import poll_check
# from .node import APNODE_ButtonScript_NodeProps


class AP_OT_create_open_wg_button_script(Operator):
    bl_label = 'Create and/or Open Script'
    bl_idname = 'armature_picker.open_wg_button_script'
    bl_description = "Create and/or Open the script from ButtonScript in a text editor"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_node=True) # APNODE_ButtonScript_NodeProps

    def execute(self, context: Context):
        active_node = context.space_data.node_tree.nodes.active
        if active_node.script_text is None:
            active_node.create_default_script()
        
        text: Text = active_node.script_text
        text.current_line_index = 0
        text.cursor_set(line=0, character=0, select=False)

        bpy.ops.wm.window_new()
        new_window = context.window_manager.windows[-1]
        new_area = new_window.screen.areas[0]
        new_area.type = 'TEXT_EDITOR'
        space_text: SpaceTextEditor = new_area.spaces[0]
        space_text.text = text
        # if space_text.top != 0:

        return {'FINISHED'}
