from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty

from .._base_wg_style import StyleBase


class PG__Image__Style(StyleBase, PropertyGroup):
    opacity: FloatProperty(
        name="Opacity",
        default=1.0,
        min=0.1,
        max=1.0
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        if not in_prefs_space:
            layout.prop(self, 'opacity')
