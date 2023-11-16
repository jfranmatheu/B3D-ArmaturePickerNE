from bpy.types import UILayout

from armature_picker.ackit import ACK
from armature_picker.utils.math import map_value
from .._base_wg_style import StyleBase


@ACK.Deco.PROP_GROUP.CHILD
class PG__SliderRadial__Style(StyleBase):

    @property
    def u_thickness(self) -> float:
        return map_value(self.bar_thickness_factor, (0, 1), (.9, 0))


    bar_thickness_factor: ACK.Prop.FACTOR("Bar Thickness", 0.15)

    color: ACK.Prop.COLOR_RGBA("Slider base color", (.21, .21, .21, 1.0))
    fill_color: ACK.Prop.COLOR_RGBA("Slider fill color", (.18, .5, 1.0, 1.0))

    bar_arc_angle: ACK.Prop.ANGLE_DEGREE("Arc Angle", default=360)

    invert_fill_flow: ACK.Prop.BOOL(
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
