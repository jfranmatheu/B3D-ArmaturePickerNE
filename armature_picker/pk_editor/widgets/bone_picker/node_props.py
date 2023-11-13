from bpy.props import PointerProperty

from .wg_style import PG__BonePicker__Style
from .._button_common import APNODE_Button_Common


class APNODE_BonePicker_NodeProps(APNODE_Button_Common):
    style: PointerProperty(name="Style", type=PG__BonePicker__Style)
