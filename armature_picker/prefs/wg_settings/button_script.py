from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, EnumProperty

from ._base import SettingsBase


class PG_ButtonScript_Settings(SettingsBase, PropertyGroup):

    def draw(self, layout: UILayout) -> None:
        pass
