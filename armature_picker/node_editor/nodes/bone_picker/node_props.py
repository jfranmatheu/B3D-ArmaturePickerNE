from bpy.types import Context, UILayout, Armature, Image
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from math import ceil

from ....utils.math import clamp



class APNODE_BonePicker_NodeProps:

    def update_dimensions(self, context: Context) -> None:
        if self.use_image and self.image is not None:
            self.image: Image
            w, h = self.image.size
            self.rect_transform.dimensions = (
                int(w * self.image_scale[0]),
                int(h * (self.image_scale[0] if self.keep_aspect_ratio else self.image_scale[1]))
            )
            return

        if self.fit_to_text and self.label == '':
            return

        ui_scale = context.preferences.system.ui_scale
        padding = 4 * ui_scale
        padding *= 2

        if self.fit_to_text:
            self.rect_transform.dimensions = (
                ceil(self.label_dimensions[0] + padding),
                ceil(self.label_dimensions[1] + padding)
            )

        else:
            # USER-EDITED-DIMENSIONS: self.edit_dimensions
            # INTERNAL DIMENSIONS: self.dimensions
            self.rect_transform.dimensions = (
                ceil(clamp(max(self.rect_transform.edit_dimensions[0], 10), self.label_dimensions[0] + padding, 500)),
                ceil(clamp(max(self.rect_transform.edit_dimensions[1], 10), self.label_dimensions[1] + padding, 500))
            )

    def update_fit_to_text(self, context: Context) -> None:
        ui_scale = context.preferences.system.ui_scale
        padding = 4 * ui_scale
        padding *= 2

        self.rect_transform.edit_dimensions = (
            ceil(clamp(max(self.rect_transform.edit_dimensions[0], 10), self.label_dimensions[0] + padding, 500)),
            ceil(clamp(max(self.rect_transform.edit_dimensions[1], 10), self.label_dimensions[1] + padding, 500))
        )


    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_label(self, context: Context) -> None:
        set_text_size(0, self.text_size)
        self.label_dimensions = get_text_dimensions(0, self.label)

        self.update_dimensions(context)
        self.dirty_label = True
        self.update_graphics(context)

    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    fit_to_text: BoolProperty(
        name="Fit To Text",
        description="Whether to fit button dimensions to label text box size",
        default=True,
        update=update_fit_to_text
    )

    label_dimensions: FloatVectorProperty(
        name="Label Dimensions",
        min=0,
        size=2,
        subtype='XYZ',
        options={'HIDDEN'}
    )

    label: StringProperty(
        name="Label",
        description="Button label",
        update=update_label,
        options={'TEXTEDIT_UPDATE'}
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

    image_scale: FloatVectorProperty(
        name="Image Scale",
        default=(1, 1),
        min=0.1,
        max=10,
        size=2,
        subtype='XYZ',
        update=update_dimensions
    )

    keep_aspect_ratio: BoolProperty(
        name="Keep aspect ratio",
        default=True,
        update=update_dimensions
    )

    
    # ------ Draw UILayout --------------------------------

    def draw_label_props(self, layout: UILayout) -> None:
        layout.prop(self, 'label', text="Text")

        layout.separator()

        layout.prop(self, 'text_size')
        _sub = layout.row()
        _sub.enabled = not self.fit_to_text
        _sub.prop(self, 'text_alignment')
