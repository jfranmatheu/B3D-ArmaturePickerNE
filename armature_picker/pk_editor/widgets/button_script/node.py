import bpy
from mathutils import Vector
from bpy.types import Text, UILayout

from textwrap import wrap

from .._base import AP_Node, Context, Event, Node
from .node_props import APNODE_ButtonScript_NodeProps, PG__ButtonScript__Style
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

    def copy(self, node):
        super().copy(node)

        if self.button_type == 'SCRIPT':
            if self.script_text is not None:
                script_text_copy = self.script_text.copy()
                script_text_copy.name = '.' + self.uuid
                self.script_text = script_text_copy
            else:
                self.create_default_script()


    def init_script_button(self, context: Context):
        self.button_type = 'SCRIPT'
        self.label = 'Run Script'
        self.create_default_script()

    def init_operator_button(self, context: Context):
        self.button_type = 'OPERATOR'
        self.label = 'Run Operator'
        self.op_idname = 'render.render'


    def create_default_script(self) -> None:
        self.script_text: Text = bpy.data.texts.new('.' + self.uuid)
        self.script_text.from_string(script_text_template)

    def draw_error_message(self, popover, context: Context) -> None:
        layout: UILayout = popover.layout
        lines = wrap(self.error_message, 40)
        for line in lines:
            layout.label(text=line)

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE':
            self.set_hovered(False)
            context.region.tag_redraw()

        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':

            view3d_context = get_view3d_context(context)
            if view3d_context is None:
                self.error_message = "Bad context!\nCould not find a 3D Viewport"
                context.window_manager.popover(self.draw_error_message)
                return {'CANCELLED'}
            
            armature_object = context.active_object

            if self.button_type == 'SCRIPT':
                script_text: Text = self.script_text
                d = {'armature': armature_object.data, 'pose': armature_object.pose}
                command = lambda : exec(script_text.as_string(), d, d)

            elif self.button_type == 'OPERATOR':
                if self.invalid_command:
                    return {'CANCELLED'}
                if self.operator is not None:
                    command = self.operator.run_invoke
                else:
                    command = lambda : exec(f"bpy.ops.{self.op_idname}('INVOKE_DEFAULT')")

            try:
                with context.temp_override(**view3d_context, armature=armature_object.data):
                    command()
            except Exception as e:
                print(e)
                self.error_message = e.__str__()
                context.window_manager.popover(self.draw_error_message)

            return {'FINISHED'}
