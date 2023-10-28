import bpy
from mathutils import Vector
from bpy.types import Text, UILayout

from textwrap import wrap

from .._base import AP_Node, Context, Event, Node
from .node_props import APNODE_ButtonScript_NodeProps, ButtonScript_Style
from armature_picker.utils.view3d import get_view3d_context


script_text_template = """# GLOBAL VARIABLES:
# You can use the following variables organically in your script:
# - armature
# - pose

import bpy

# Get pose bone:
# pose.bones['Bone']
"""


class APNODE_ButtonScript(APNODE_ButtonScript_NodeProps, AP_Node, Node):
    bl_idname = 'AP_NODE_button_script'
    bl_label = 'Button Script'
    bl_icon = 'FILE_SCRIPT'
    wg_type = 'button_script'

    def init(self, context):
        super().init(context)

        self.label = 'Run Script'
        self.create_default_script()

    def copy(self, node):
        super().copy(node)

        if self.script_text is not None:
            script_text_copy = self.script_text.copy()
            script_text_copy.name = '.' + self.uuid
            self.script_text = script_text_copy
        else:
            self.create_default_script()

    def create_default_script(self) -> None:
        self.script_text: Text = bpy.data.texts.new('.' + self.uuid)
        self.script_text.from_string(script_text_template)

    def draw_error_message(self, popover, context: Context) -> None:
        layout: UILayout = popover.layout
        lines = wrap(self.error_message, 40)
        for line in lines:
            layout.label(text=line)

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            script_text: Text = self.script_text
            view3d_context = get_view3d_context(context)
            ## print(script_text.as_string())
            try:
                with context.temp_override(**view3d_context):
                    armature_object = context.active_object
                    d = {'armature': armature_object.data, 'pose': armature_object.pose}
                    exec(script_text.as_string(), d, d)
            except Exception as e:
                print(e)
                self.error_message = e.__str__()
                context.window_manager.popover(self.draw_error_message)
            return {'FINISHED'}
