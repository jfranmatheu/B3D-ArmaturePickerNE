from bpy.types import PropertyGroup, UILayout
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty

from armature_picker.utils.math import map_value
from .._base_wg_style import StyleBase


class PG__SliderRadial__Style(StyleBase, PropertyGroup):

    @property
    def u_thickness(self) -> float:
        return map_value(self.bar_thickness_factor, (0, 1), (.9, 0))


    bar_thickness_factor: FloatProperty(
        name="Bar Thickness",
        description="From available radius, between 0 and 1, decide the thickness of the slider bar",
        default=0.15,
        min=0.0,
        max=1.0
    )

    color: FloatVectorProperty(
        name="Color",
        description="Slider base color",
        default=(.281, .281, .281, .9),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    fill_color: FloatVectorProperty(
        name="Fill Color",
        description="Slider fill color",
        default=(.212, .63, 1.0, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    bar_arc_angle: FloatProperty(
        name="Arc Angle",
        description="The angle of the arc. 360 for a closed slider_radial slider, less than 360 for an arc slider",
        default=360,
        min=0,
        max=360
    )

    invert_fill_flow: BoolProperty(
        name="Invert Fill Flow",
        default=False
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        col = layout.column()
        col.prop(self, 'bar_thickness_factor')
        col.prop(self, 'bar_arc_angle')
        col.prop(self, 'invert_fill_flow')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'fill_color')
