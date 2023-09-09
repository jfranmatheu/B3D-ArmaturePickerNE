from bpy.types import Context, UILayout, Image
from bpy.props import PointerProperty, BoolProperty



class APNODE_Image_NodeProps:

    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_image(self, context: Context) -> None:
        self.update_dimensions(context)

        self.label = 'No Image' if self.image is None else self.image.name

    def update_dimensions(self, context: Context) -> None:
        if self.image is not None:
            self.image: Image
            w, h = self.image.size
            self.dimensions = (
                w * self.scale[0],
                h * (self.scale[0] if self.keep_aspect_ratio else self.scale[1])
            )

        else:
            self.dimensions = (
                20, 20
            )


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    image: PointerProperty(
        name="Image",
        type=Image,
        update=update_image,
    )
    
    keep_aspect_ratio: BoolProperty(
        name="Keep aspect ratio",
        default=True,
        update=update_dimensions
    )

    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'image')
