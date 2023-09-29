from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty

from ._base import SettingsBase


class PG_Label_Settings(SettingsBase, PropertyGroup):
    
    def draw(self, layout: UILayout) -> None:
        pass
