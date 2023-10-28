from ._base import Context, UILayout
from ._transform_props import RectTransform

from bpy.types import Context, UILayout, Image
from mathutils import Vector, Matrix
import gpu
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, FloatVectorProperty, EnumProperty, PointerProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from math import ceil

from ...utils.math import clamp
from ...utils.ui_layout import draw_section
from armature_picker.prefs.styles._common_button import CommonTheme__Button
from ...gpu import draw
from ...utils.geometry import rotate_point, point_inside_rect


pick_color_buffer = gpu.types.Buffer('FLOAT', 4, (0, 0, 0, 0))



class APNODE_Button_CommonProps:
    style: CommonTheme__Button


    def get_style(self, theme) -> CommonTheme__Button:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)


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
        
    def update_aspect_ratio(self, context: Context) -> None:
        if not self.keep_aspect_ratio:
            self.image_scale_x, self.image_scale_y = 1, 1
        else:
            self.image_scale_x, self.image_scale_y = 1, 1


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
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

    # image_scale: FloatProperty(
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
        max=10,
        update=update_dimensions
    )

    image_scale_y: FloatProperty(
        name="Image Scale Y",
        default=1,
        min=0.1,
        max=10,
        update=update_dimensions
    )

    keep_aspect_ratio: BoolProperty(
        name="Keep aspect ratio",
        default=True,
        update=update_aspect_ratio
    )


    # ------ Draw UILayout --------------------------------

    def draw_button_props(self, context: Context, panel_layout: UILayout) -> None:
        # DRAW LABEL PROPS.
        style_section = draw_section(panel_layout, 'Label', icon='FILE_TEXT')
        if self.use_image:
            style_section.enabled = False
        style_section.prop(self, 'label', text="Text")
        style_section.separator()
        style_section.prop(self, 'text_size')
        _sub = style_section.row()
        _sub.enabled = not self.fit_to_text
        _sub.prop(self, 'text_alignment')

        # DRAW IMAGE GRAPHICS PROPS.
        image_section = draw_section(panel_layout, 'Image Graphic', icon='IMAGE_DATA')
        row = image_section.row(align=True, heading='Image')
        row.prop(self, 'use_image', text="")
        _row = row.row(align=True)
        _row.enabled = self.use_image
        _row = _row.row(align=True)
        _row.prop(self, 'image', text='')
        _row.operator('armature_picker.load_image_for_active_node', text='', icon='IMPORT')


    def draw_styles(self, panel_layout: UILayout, section_layout: UILayout) -> None:
        if self.use_image:
            section_layout.enabled = False

        super().draw_styles(panel_layout, section_layout)



class APNODE_Button_Common(APNODE_Button_CommonProps):

    # ----- ON HOVER --------------------------------

    def on_hover(self, context: Context, in_edit: bool, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
            if self.use_image and self.image is not None and self.node_tree.picker_mode == 'POSE':

                ## bbox_n = rect.bound_box_norm
                bbox_size = tuple(int(v) for v in (rect.bound_box_size))
                ## coords_rot_n = rect.coords_rotated_norm
                mpos_in_bbox_space = rect.convert_abs_coord_to_rel_coord(region_loc, context)

                offscreen = gpu.types.GPUOffScreen(*bbox_size, format ='RGBA16F')

                ## print("BBOX Norm:", coords_rot_n, bbox_size)
                ## print("Bottom-Left:", bbox_n, " --> ", coords_rot_n)
                ## print("MousePos:", region_loc, " --> ", mpos_in_bbox_space)

                from gpu_extras.presets import draw_texture_2d

                wnd_size = context.window.width, context.window.height

                with offscreen.bind():
                    fb = gpu.state.active_framebuffer_get()
                    fb.clear(color=(0.0, 0.0, 0.0, 0.0))
                    with gpu.matrix.push_pop():
                        gpu.matrix.load_matrix(Matrix.Identity(4))
                        gpu.matrix.scale((wnd_size[0] / bbox_size[0], wnd_size[1] / bbox_size[1]))

                        draw_texture_2d(draw.get_gputex(self.image), Vector((0, 0)), *bbox_size)

                    x, y, w, h = fb.viewport_get()
                    px = (
                        mpos_in_bbox_space.x * bbox_size[0],
                        mpos_in_bbox_space.y * bbox_size[1]
                    )

                    ## print(px)

                    if rect.rotation != 0:
                        px = rotate_point(Vector(px), Vector((0, 0)), -rect.rotation)

                    px = tuple(int(v) for v in px)

                    ## print("PX:", px)

                    fb.read_color(*px, 1, 1, 4, 0, 'FLOAT', data=pick_color_buffer)

                    buffer = fb.read_color(x, y, w, h, 4, 0, 'FLOAT')
                    buffer.dimensions = bbox_size[0] * bbox_size[1] * 4

                px_alpha_value = pick_color_buffer[-1]

                if px_alpha_value <= 0.01:
                    return False

            return True
        return False


    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: CommonTheme__Button, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos: Vector = rect.position
        size: Vector = rect.size

        if self.use_image and self.image is not None:
            if active or (selected and context.mode != 'POSE'):
                draw.image_ui_outline(
                    self, 'BUTTON_IMAGE',
                    image=self.image,
                    outline_color=(1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
                )
            else:
                draw.image_ui(
                    self, 'BUTTON_IMAGE',
                    image=self.image
                )
            return


        draw.wg_ui(
            self, 'BUTTON_BASE',
            roundness=style.roundness,
            outline_thickness=style.outline_thickness,
            bg_color=style.color if not hovered else Vector(style.color) * 1.2
        )


        if self.label != '':
            padding = 4 * scale

            label_dimensions = Vector(self.label_dimensions)

            if self.fit_to_text:
                pivot = (0.5, 0.5)
                tex_pos = pos + Vector((padding, padding))
            else:
                align = self.text_alignment
                if align == 'LEFT':
                    pivot = (0.0, 0.5)
                elif align == 'CENTER':
                    pivot = (0.5, 0.5)
                elif align == 'RIGHT':
                    pivot = (1.0, 0.5)

                tex_pos = Vector((
                    pos.x + size.x * pivot[0] - label_dimensions.x * pivot[0],
                    pos.y + size.y * pivot[1] - label_dimensions.y * pivot[1],
                ))

            draw.text_cached(
                self.uuid, 'LABEL', self.dirty, self.dirty_label,
                tex_pos,
                Vector(rect.origin) if rect.rotation == 0 else rotate_point(pos + Vector((padding, padding)), Vector(rect.origin), rect.rotation),
                self.label,
                self.text_size,
                label_dimensions,
                pivot=pivot if rect.rotation == 0 else (0, 0),
                angle=rect.rotation,
                color=style.text_color,
                origin=Vector(rect.origin)
            )

    def draw__edit(self, context, view_loc: Vector, rect: RectTransform, style: CommonTheme__Button, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.use_image and self.image is not None:
            return
        super().draw__edit(context, view_loc, rect, style, wg_settings, scale, active, selected, hovered)

    def draw__pose(self, context, view_loc: Vector, rect: RectTransform, style: CommonTheme__Button, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.use_image and self.image is not None:
            return
        super().draw__pose(context, view_loc, rect, style, wg_settings, scale, active, selected, hovered)


    # ----- UI LAYOUT DRAWING -----------------------------------------------------------


    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        if self.use_image:
            layout.prop(self, 'keep_aspect_ratio', text="Keep Image Aspect Ratio")
        else:
            layout.prop(self, 'fit_to_text', text="Fit To Label Text")

        layout.separator()

        layout.row().prop(rect_transform, 'origin')
        layout.row().prop(rect_transform, 'pivot', slider=True)

        if self.use_image:
            if self.keep_aspect_ratio:
                layout.prop(self, 'image_scale_x', text='Image Scale', slider=True)
            else:
                col = layout.column(align=True, heading="Image Scale")
                col.prop(self, 'image_scale_x', text='X', slider=True)
                col.prop(self, 'image_scale_y', text='Y', slider=True)
        else:
            _sub = layout.column()
            _sub.enabled = not self.fit_to_text
            if self.fit_to_text and not self.use_image:
                _sub.row().prop(rect_transform, 'dimensions', text='Size')
            else:
                _sub.row().prop(rect_transform, 'edit_dimensions', text='Size')

        layout.prop(rect_transform, 'rotation', slider=True)

        layout.prop(self, 'draw_depth')
