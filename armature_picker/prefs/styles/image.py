from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty

from ._base import StyleBase


class PG_ArmaturePickerTheme__Image(StyleBase, PropertyGroup):
    opacity: FloatProperty(
        name="Opacity",
        default=1.0,
        min=0.1,
        max=1.0
    )
    
    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        if not in_prefs_space:
            layout.prop(self, 'opacity')
