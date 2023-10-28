from bpy.props import PointerProperty

from armature_picker.prefs.styles import BonePicker_Style
from .._button_common import APNODE_Button_Common


class APNODE_BonePicker_NodeProps(APNODE_Button_Common):
    style: PointerProperty(name="Style", type=BonePicker_Style)
