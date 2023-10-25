from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .._bone_picker_common import APNODE_BonePicker_Common
from .node_props import APNODE_BonePicker_NodeProps, BonePicker_Style

from bpy.types import Context, UILayout
from mathutils import Vector, Matrix
import gpu

from ....gpu import draw
from ....utils.geometry import rotate_point, point_inside_rect, get_center, point_inside_circle


pick_color_buffer = gpu.types.Buffer('FLOAT', 4, (0, 0, 0, 0))



class AP_BonePickerNode(APNODE_BonePicker_NodeProps, APNODE_BonePicker_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker'
    bl_label = 'Bone Picker'
    bl_icon = 'CONSTRAINT_BONE'
    wg_type = 'bone_picker'


    def get_ikfk_pos_size(self, apply_rotation: bool = False, center: bool = False):
        rect: RectTransform = self.rect_transform
        if self.fit_to_text:
            ikfk_size = Vector((rect.dimensions[1], rect.dimensions[1]))
            if center:
                ikfk_pos = rect.get_point_relative(1.0, 0.5, offset=Vector((ikfk_size.x * 0.5, 0)), apply_rotation=True, rotate_from_origin=True)
            else:
                ikfk_pos = rect.get_point_relative(1.0, 0.0, apply_rotation=apply_rotation)
        else:
            size = min(rect.dimensions[1], self.ik_fk_size)
            ikfk_size = Vector((size, size))
            if center:
                ikfk_pos = rect.get_point_relative(1.0, 0.5, offset=Vector((size*.7, 0)), apply_rotation=True, rotate_from_origin=True)
            else:
                ikfk_pos = rect.get_point_relative(1.0, 0.5, offset=Vector((size*0.2, -size*0.5)), apply_rotation=apply_rotation)
        return ikfk_pos, ikfk_size


    # ----- ON HOVER --------------------------------

    def on_hover(self, context: Context, in_edit: bool, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
            self.set_state('ik_fk_hovered', False)
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
        elif self.use_ik_fk:
            ikfk_pos, ikfk_size = self.get_ikfk_pos_size(center=True)
            if point_inside_circle(view_loc, ikfk_pos, ikfk_size.x * 0.5):
                self.set_state('ik_fk_hovered', True)
                return True
        return False


    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, style: BonePicker_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos: Vector = rect.position
        size: Vector = rect.size

        if self.use_ik_fk:
            ikfk_pos, ikfk_size = self.get_ikfk_pos_size(apply_rotation=False)

            ikfk_hovered = self.get_state('ik_fk_hovered', False)
            ikfk_state = self.get_ik_fk_state(context)

            draw.wg(
                self, 'IKFK_BASE',
                ikfk_pos, ikfk_size, rect.rotation,
                origin=Vector(rect.origin),
                roundness=1, # if ikfk_hovered else self.roundness,
                outline_thickness=1.5,
                bg_color=(.1, .1, .1, .9) if ikfk_hovered else (.05, .05, .05, .8),
            )

            ikfk_pos = get_center(ikfk_pos, ikfk_size)
            ikfk_size *= 0.5

            draw.wg(
                self, 'IKFK_TOGGLE',
                ikfk_pos-ikfk_size*0.5, ikfk_size, rect.rotation,
                origin=Vector(rect.origin),
                roundness=1,
                outline_thickness=0,
                bg_color=(.1, .5, 1.0, .9) if ikfk_state else (.5, .5, .5, .9),
            )


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

    def draw__edit(self, context, rect: RectTransform, style: BonePicker_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.use_image and self.image is not None:
            return
        super().draw__edit(context, rect, style, wg_settings, scale, active, selected, hovered)

    def draw__pose(self, context, rect: RectTransform, style: BonePicker_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.use_image and self.image is not None:
            return
        super().draw__pose(context, rect, style, wg_settings, scale, active, selected, hovered)


    # ----- UI LAYOUT DRAWING -----------------------------------------------------------


    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        row = layout.row()
        row.enabled = not self.use_image
        row.prop(self, 'fit_to_text')

        layout.separator()

        layout.row().prop(rect_transform, 'origin')
        layout.row().prop(rect_transform, 'pivot')

        if self.use_image:
            layout.prop(self, 'keep_aspect_ratio')
            layout.prop(self, 'image_scale')
        else:
            _sub = layout.column()
            _sub.enabled = not self.fit_to_text
            if self.fit_to_text and not self.use_image:
                _sub.row().prop(rect_transform, 'dimensions', text='Size')
            else:
                _sub.row().prop(rect_transform, 'edit_dimensions', text='Size')

        layout.prop(rect_transform, 'rotation')

        layout.prop(self, 'draw_depth')
