from bpy.types import Context, UILayout, Image
from bpy.props import PointerProperty, BoolProperty, FloatVectorProperty

from armature_picker.prefs.styles import Image_Style


class APNODE_Image_NodeProps:
    def get_style(self, theme) -> Image_Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=Image_Style)

    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_image(self, context: Context) -> None:
        self.update_dimensions(context)

        self.label = 'No Image' if self.image is None else self.image.name

    def update_dimensions(self, context: Context) -> None:
        if self.image is not None:
            self.image: Image
            w, h = self.image.size
            self.rect_transform.dimensions = (
                int(w * self.image_scale[0]),
                int(h * (self.image_scale[0] if self.keep_aspect_ratio else self.image_scale[1]))
            )

        else:
            self.rect_transform.dimensions = (
                20, 20
            )

        self.update_graphics(context)


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    image: PointerProperty(
        name="Image",
        type=Image,
        update=update_image,
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

    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        row = layout.row(align=True)
        row.prop(self, 'image')
        row.operator('armature_picker.load_image_for_active_node', text='', icon='IMPORT')
