from bpy.props import PointerProperty
from bpy.types import Text, Context, UILayout

from armature_picker.prefs.styles import ButtonScript_Style
from .._button_common import APNODE_Button_Common
from .button_script_ops import AP_OT_create_open_wg_button_script


class APNODE_ButtonScript_NodeProps(APNODE_Button_Common):
    style: PointerProperty(name="Style", type=ButtonScript_Style)
    script_text: PointerProperty(name="Script", description="Script Text Datablock", type=Text)


    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        # layout.prop(self, 'script_text', icon='TEXT')
        layout.scale_y = 1.5
        layout.operator(AP_OT_create_open_wg_button_script.bl_idname,
                        text="Open Script" if self.script_text is not None else "Create Script",
                        icon='TEXT')
