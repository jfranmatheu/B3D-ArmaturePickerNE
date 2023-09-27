from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatVectorProperty, BoolProperty

from ._base import StyleBase


class PG_ArmaturePickerTheme__BonePickerGeo(StyleBase, PropertyGroup):
    color: FloatVectorProperty(
        name="Background Color",
        description="Background Color of the button",
        default=(.05, .51, .95, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    display_on_hover_only: BoolProperty(name="Show only on hover", description="(While in POSE mode) Display this element only when hovering over it", default=False)

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        layout.prop(self, 'display_on_hover_only')
        layout.prop(self, 'color')
