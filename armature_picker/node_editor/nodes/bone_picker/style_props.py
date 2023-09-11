from bpy.types import Context, UILayout, Image
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty

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
        default=(.9, .52, .41, 1.0),
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

    text_alignment: EnumProperty(
        name="Text Alignment",
        items=(
            ('LEFT', 'Left', ""),
            ('CENTER', 'Center', ""),
            ('RIGHT', 'Right', "")
        ),
        default='CENTER',
        update=lambda node, ctx: node.update_graphics(ctx)
    )

    text_color: FloatVectorProperty(
        name='Text Color',
        description="Label text color",
        default=(.0, .0, .0, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR',
        update=lambda node, ctx: node.update_label(ctx)
    )

    roundness: FloatProperty(
        name="Roundness",
        description="Roundness of the button",
        min=0,
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

    use_image: BoolProperty(
        name="Use Image",
        description="Use Image graphics instead",
        default=False,
        update=lambda node, ctx: node.update_graphics(ctx)
    )

    image: PointerProperty(
        name="Image",
        description="When using image graphic, the rest of styles are not used. The picker will ignore transparent pixels ;-)",
        type=Image,
        update=lambda node, ctx: node.update_graphics(ctx)
    )

    def draw_styles(self, layout: UILayout) -> None:
        row = layout.row(align=True, heading='Image')
        row.prop(self, 'use_image', text="")
        _row = row.row(align=True)
        _row.enabled = self.use_image
        _row.prop(self, 'image', text="")

        col = layout.column()
        if self.use_image:
            col.enabled = False
        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'text_color')
