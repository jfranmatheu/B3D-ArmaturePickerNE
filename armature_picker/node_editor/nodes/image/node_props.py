from bpy.types import Context, UILayout, Image
from bpy.props import PointerProperty, BoolProperty, FloatProperty, FloatVectorProperty
from mathutils import Vector

from .._transform_props import RectTransform
from armature_picker.prefs.styles import Image_Style


class APNODE_Image_NodeProps:
    def get_style(self, theme) -> Image_Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=Image_Style)

    # ----- TRANSFORM CONSTRAINTS --------------------------------

    def apply_transform_dimensions_constraints(self, prev_dimensions: Vector, new_dimensions: Vector) -> None:
        if self.image is None:
            return
        if not self.keep_aspect_ratio:
            return
        _w, _h = prev_dimensions
        w, h = new_dimensions
        if w == _w and h == _h:
            return

        # origin = tuple(self.rect_transform.origin)

        old_image_scale_x = self.image_scale_x

        if w != _w:
            old_width = prev_dimensions.x
            new_width = new_dimensions.x
            # old_width --> old_image_scale_x
            # new_width --> new_image_scale_x
            new_image_scale_x = old_image_scale_x * new_width / old_width

        elif h != _h:
            old_image_scale_y = self.image_scale_y
            old_height = prev_dimensions.y
            new_height = new_dimensions.y
            # old_height --> old_image_scale_Y
            # new_height --> new_image_scale_Y
            new_image_scale_y = old_image_scale_y * new_height / old_height

            if new_image_scale_y < 0.1:
                new_image_scale_y = 0.1
            if new_image_scale_y != old_image_scale_y:
                self.image_scale_y = new_image_scale_y
                # self.rect_transform.origin = origin

            img_w, img_h = self.image.size
            aspect_ratio = img_w / img_h
            new_image_scale_x = new_image_scale_y * aspect_ratio
        else:
            return

        if new_image_scale_x < 0.1:
            new_image_scale_x = 0.1
        if new_image_scale_x == old_image_scale_x:
            return
        self.image_scale_x = new_image_scale_x

        # self.rect_transform.origin = origin


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
                int(w * self.image_scale_x),
                int(h * (self.image_scale_x if self.keep_aspect_ratio else self.image_scale_y))
            )

        else:
            self.rect_transform.dimensions = (
                20, 20
            )

        self.update_graphics(context)


    def update_aspect_ratio(self, context: Context) -> None:
        self.update_dimensions(context)
        return
        if not self.keep_aspect_ratio:
            self.image_scale_x, self.image_scale_y = 1, 1
        else:
            self.image_scale_x, self.image_scale_y = 1, 1


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    image: PointerProperty(
        name="Image",
        type=Image,
        update=update_image,
    )

    # image_scale: FloatVectorProperty(
    #     name="Image Scale",
    #     default=(1, 1),
    #     min=0.1,
    #     max=10,
    #     size=2,
    #     subtype='XYZ',
    #     update=update_dimensions
    # )

    image_scale_x: FloatProperty(
        name="Image Scale X",
        default=1,
        min=0.1,
        max=2,
        update=update_dimensions
    )

    image_scale_y: FloatProperty(
        name="Image Scale Y",
        default=1,
        min=0.1,
        max=2,
        update=update_dimensions
    )

    keep_aspect_ratio: BoolProperty(
        name="Keep aspect ratio",
        default=True,
        update=update_aspect_ratio
    )

    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        row = layout.row(align=True)
        row.prop(self, 'image')
        row.operator('armature_picker.load_image_for_active_node', text='', icon='IMPORT')
