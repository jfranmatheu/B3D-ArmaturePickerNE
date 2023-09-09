from bpy.types import Context, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty

from ....utils.ui_layout import draw_section


class APNODE_Label_StyleProps:

    # STYLE PROPERTIES
    # ----------------------------------------------------------------

    text_size: IntProperty(
        name='Text Size',
        description="Label text size",
        default=16,
        min=10,
        update=lambda node, ctx: node.update_label(ctx)
    )

    text_color: FloatVectorProperty(
        name='Text Color',
        description="Label text color",
        default=(1, 1, 1, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    def draw_styles(self, layout: UILayout) -> None:
        layout.prop(self, 'text_size')
        layout.prop(self, 'text_color')
