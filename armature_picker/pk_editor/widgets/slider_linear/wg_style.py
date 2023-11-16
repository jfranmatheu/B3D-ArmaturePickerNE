from bpy.types import UILayout

from armature_picker.ackit import ACK
from .._base_wg_style import StyleBase, call_active_node_func


@ACK.Deco.PROP_GROUP.CHILD
class PG__SliderLinear__Style(StyleBase):
    show_handle: ACK.Prop.BOOL(
        name="Show Handle",
        description="Show slider handle",
        default=True,
        update=call_active_node_func('update_handle_pos')
    )

    handle_type: ACK.Prop.ENUM(
        name="Handle Type",
        items=(
            ('CIRCLE', "Circle", "Circular shape", 'RADIOBUT_ON', 0),
            ('LINE', "Line", "Line shape", 'FIXED_SIZE', 1),
        ),
        default='CIRCLE',
        update=call_active_node_func('update_handle_pos')
    )

    bar_line_thickness: ACK.Prop.FLOAT(
        name="Bar Thickness",
        description="Bar Line type thickness",
        default=1.5,
        min=1,
        max=5,
        update=call_active_node_func('update_graphics')
    )

    bar_type: ACK.Prop.ENUM(
        name="Bar Type",
        items=(
            ('FILL', "Fill", "Fill shape"),
            ('LINE', "Line", "Line shape"),
        ),
        default='FILL',
        update=call_active_node_func('update_graphics')
    )

    color: ACK.Prop.COLOR_RGBA("Slider base color", (.21, .21, .21, 1.0))
    fill_color: ACK.Prop.COLOR_RGBA("Slider fill color", (.18, .5, 1.0, 1.0))
    handle_color: ACK.Prop.COLOR_RGBA("Slider handle color", (.8, .8, .8, 1.0))
    outline_color: ACK.Prop.COLOR_RGBA("Outline Color", (.8, .6, .2, .9))

    roundness: ACK.Prop.FLOAT(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=1,
        precision=2
    )

    outline_thickness: ACK.Prop.FLOAT(
        name="Outline Thickness",
        description="Ouline thickness of the button",
        min=0,
        max=20,
        default=1.5,
        precision=1
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
