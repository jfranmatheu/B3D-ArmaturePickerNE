from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, EnumProperty

from ._base import StyleBase, call_active_node_func


class PG_ArmaturePickerTheme__SliderLinear(StyleBase, PropertyGroup):
    show_handle: BoolProperty(
        name="Show Handle",
        description="Show slider handle",
        default=True,
        update=call_active_node_func('update_handle_pos')
    )

    handle_type: EnumProperty(
        name="Handle Type",
        items=(
            ('CIRCLE', "Circle", "Circular shape", 'RADIOBUT_ON', 0),
            ('LINE', "Line", "Line shape", 'FIXED_SIZE', 1),
        ),
        default='CIRCLE',
        update=call_active_node_func('update_handle_pos')
    )

    bar_line_thickness: FloatProperty(
        name="Bar Thickness",
        description="Bar Line type thickness",
        default=1.5,
        min=1,
        max=5,
        update=call_active_node_func('update_graphics')
    )

    bar_type: EnumProperty(
        name="Bar Type",
        items=(
            ('FILL', "Fill", "Fill shape"),
            ('LINE', "Line", "Line shape"),
        ),
        default='FILL',
        update=call_active_node_func('update_graphics')
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

    handle_color: FloatVectorProperty(
        name="Handle Color",
        description="Slider handle color",
        default=(.8, .8, .8, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    roundness: FloatProperty(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=1,
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
        layout.row().prop(self, 'bar_type', expand=True)

        layout.separator()

        col = layout.column(align=True)

        if self.bar_type == 'FILL':
            col.prop(self, 'roundness')
            col.prop(self, 'outline_thickness')

            col.separator()

            col.prop(self, 'color')
            col.prop(self, 'fill_color')

            col.separator()

            row = col.row(align=True, heading='Handle')
            row.prop(self, 'show_handle', text='')
            _row = row.row(align=True)
            _row.enabled = self.show_handle
            _row.prop(self, 'handle_color',  text='')
            _row.prop(self, 'handle_type',  text='', icon_only=True)

        elif self.bar_type == 'LINE':
            col.prop(self, 'bar_line_thickness')

            col.separator()

            col.prop(self, 'color')

            col.separator()

            row = col.row(align=True)
            row.prop(self, 'handle_color',  text='Handle')
            row.prop(self, 'handle_type',  text='', icon_only=True)
