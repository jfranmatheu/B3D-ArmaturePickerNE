from bpy.types import Context, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty

from ....utils.ui_layout import draw_section


class APNODE_BonePicker_StyleProps:

    # STYLE PROPERTIES
    # ----------------------------------------------------------------
    fit_to_text: BoolProperty(
        name="Fit To Text",
        description="Whether to fit button dimensions to label text box size",
        default=True,
        update=lambda node, ctx: node.update_dimensions(ctx)
    )

    color: FloatVectorProperty(
        name="Background Color",
        description="Background Color of the button",
        default=(1, .8, .4, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    text_size: IntProperty(
        name='Text Size',
        description="Label text size",
        default=12,
        min=10,
        update=lambda node, ctx: node.update_label(ctx)
    )

    text_color: FloatVectorProperty(
        name='Text Color',
        description="Label text color",
        default=(.0, .0, .0, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    def draw_styles(self, layout: UILayout) -> None:
        layout.prop(self, 'fit_to_text')
        layout.separator()
        layout.prop(self, 'color')
        layout.prop(self, 'text_size')
        layout.prop(self, 'text_color')
