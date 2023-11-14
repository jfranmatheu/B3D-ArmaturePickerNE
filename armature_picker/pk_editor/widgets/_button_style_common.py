from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, EnumProperty

from ._base_wg_style import StyleBase, call_active_node_func, use_active_node


class CommonTheme__Button(StyleBase):

    roundness: FloatProperty(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=.5,
        precision=2
    )

    outline_thickness: FloatProperty(
        name="Outline Thickness",
        description="Ouline thickness of the button",
        min=0,
        max=20,
        default=1.5,
        precision=1
    )

    outline_color: FloatVectorProperty(
        name="Outline Color",
        description="Outline Color of the button",
        default=(.8, .6, .2, .9),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        col = layout.column()

        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'text_color')
