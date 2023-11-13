from bpy.types import PropertyGroup, UILayout
from bpy.props import FloatVectorProperty

from .._base_wg_style import StyleBase


class PG__Label__Style(StyleBase, PropertyGroup):
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
