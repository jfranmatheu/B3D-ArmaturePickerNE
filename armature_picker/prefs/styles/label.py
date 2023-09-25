from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty

from ._base import StyleBase


class PG_ArmaturePickerTheme__Label(StyleBase, PropertyGroup):
    text_color: FloatVectorProperty(
        name="Text Color",
        description="Label Text Color",
        default=(.92, .92, .92, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )


    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        layout.prop(self, 'text_color')
