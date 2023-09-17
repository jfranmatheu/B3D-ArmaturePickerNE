from bpy.types import Context, UILayout, Image
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty

from .....utils.math import map_value


class APNODE_SliderRadial_StyleProps:

    # STYLE PROPERTIES
    # ----------------------------------------------------------------
    @property
    def u_thickness(self) -> float:
        return map_value(self.bar_thickness_factor, (0, 1), (.9, 0))


    bar_thickness_factor: FloatProperty(
        name="Bar Thickness",
        description="From available radius, between 0 and 1, decide the thickness of the slider bar",
        default=0.2,
        min=0.0,
        max=1.0
    )

    bar_arc_angle_range: FloatVectorProperty(
        name="Arc Angle Range",
        description="The angle range of the arc. 360 for a closed radial slider, less than 360 for an arc slider",
        default=(-135, 135),
        size=2,
        min=-180,
        max=180
    )


    def draw_styles(self, layout: UILayout) -> None:
        col = layout.column()
        col.prop(self, 'bar_thickness_factor')
        col.prop(self, 'bar_arc_angle_range')

        col.separator()

        col.prop(self, 'bar_type')
        col.prop(self, 'color')
        if self.bar_type == 'FILL':
            col.prop(self, 'fill_color')
        elif self.bar_type == 'LINE':
            col.prop(self, 'bar_line_thickness')

        col.separator()

        row = col.row(align=True, heading='Handle')
        row.prop(self, 'show_handle', text='')
        _row = row.row(align=True)
        _row.enabled = self.show_handle
        _row.prop(self, 'handle_color',  text='')
        _row.prop(self, 'handle_type',  text='', icon_only=True)
