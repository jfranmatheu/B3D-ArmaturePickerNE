from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .node_props import APNODE_BonePicker_NodeProps
from .style_props import APNODE_BonePicker_StyleProps

import numpy as np

import bpy
from bpy.types import Context, Armature, Bone, Event, UILayout, Image
from mathutils import Vector, Matrix
import gpu

from ....gpu import draw
from ....utils.geometry import rotate_point, point_inside_rect, get_center, get_point_in_rect_space
from ....utils.math import clamp, rotate_vector
from ....utils.armature import deselect_all_bones_from_active
from ....utils.node_editor import get_node_editor_view_point


pick_color_buffer = gpu.types.Buffer('FLOAT', 4, (0, 0, 0, 0))
# pick_depth_buffer = gpu.types.Buffer('FLOAT', 1, (0,))


class AP_BonePickerNode(APNODE_BonePicker_NodeProps, APNODE_BonePicker_StyleProps, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker'
    bl_label = 'Bone Picker'
    bl_icon = 'CONSTRAINT_BONE'

    draw_layer = 10


    def init(self, context):
        super().init(context)

        self.set_state('ik_fk_hovered', False)


    def get_ik_fk_state(self, context: Context) -> bool:
        if bone := self.get_bone(context, from_pose_data = True):
            if self.ik_fk_prop_idname in bone:
                return bool(bone[self.ik_fk_prop_idname])
        return False

    def toggle_ik_fk(self, context: Context) -> bool:
        if bone := context.active_pose_bone:
            if bone.name != self.bone_name:
                bone = context.active_object.pose.bones.get(self.bone_name, None)
                if bone is None:
                    return False
            if self.ik_fk_prop_idname in bone:
                bone[self.ik_fk_prop_idname] = not bool(bone[self.ik_fk_prop_idname])
        return False


    # ----- SELECT METHODS --------------------------------

    def get_bone(self, context: Context, from_pose_data: bool = False) -> Bone:
        armature: Armature = context.active_object.data
        if from_pose_data:
            bones = context.active_object.pose.bones
        else:
            bones = armature.bones if context.mode == 'POSE' else armature.edit_bones
        return bones.get(self.bone_name, None)

    def select_bone(self, context: Context, deselect_all: bool = True) -> None:
        armature: Armature = context.active_object.data
        bones = armature.bones if context.mode == 'POSE' else armature.edit_bones
        bone: Bone
        if bone := self.get_bone(context):
            if deselect_all:
                deselect_all_bones_from_active(context)
            bone.select = True
            bones.active = bone

    def on_hover(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
            self.set_state('ik_fk_hovered', False)
            if self.use_image and self.image is not None and context.mode == 'POSE':

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

                ## print("ALPHA:", px_alpha_value)

                ## def put_fucking_pixels_puto_blender_de_mierda():
                ##     image = bpy.data.images.get('tmp', None)
                ##     if image is None:
                ##         image = bpy.data.images.new('tmp', *bbox_size, alpha=True)
                ##     else:
                ##         image.scale(*bbox_size)
                ##     image.pixels = [v for v in buffer]
                ## if not bpy.app.timers.is_registered(put_fucking_pixels_puto_blender_de_mierda):
                ##     bpy.app.timers.register(put_fucking_pixels_puto_blender_de_mierda)

                '''
                view_loc_t = view_loc.copy()

                image: Image = self.image
                real_width, real_height = image.size
                draw_width, draw_height = rect.size

                scale_x = real_width / draw_width
                scale_y = real_height / draw_height

                view_loc_t -= rect.bottom_left
                # view_loc_t.normalize()
                # min_co = min(*view_loc_t)
                # view_loc_t.x += min_co
                # view_loc_t.y += min_co

                px_x = int(clamp(view_loc_t.x * scale_x, 0, real_width-1))
                px_y = int(clamp(view_loc_t.y * scale_y, 0, real_height-1))

                resolution = real_width * real_height
                colors = np.zeros(resolution * 4, dtype=np.float32)
                image.pixels.foreach_get(colors)
                colors = colors.reshape((real_width, real_height, 4))
                # px_alpha_value = image.pixels[-px_x*px_y*4+3] # colors[px_x][px_y][-1] # image.pixels[px_x*px_y*4+3] # arr[px_x][px_y][-1] # image.pixels[px_x*px_y*4]
                px_alpha_value = colors[px_x][px_y][-1]
                '''

                if px_alpha_value <= 0.01:
                    return False

            return True
        elif self.use_ik_fk:
            size = Vector((rect.dimensions[1], 0)) + rect.size
            if point_inside_rect(view_loc, rect.bottom_left, size, rect.rotation, origin=Vector(rect.origin)):
                self.set_state('ik_fk_hovered', True)
                return True
        return False

    def on_hover_exit(self, context: Context | None = None) -> None:
        self.set_state('ik_fk_hovered', False)


    # ----- INVOKE --------------------------------

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            if self.get_state('ik_fk_hovered'):
                self.toggle_ik_fk(context)
                return
            self.select_node(context, deselect_all=not event.shift)
            self.select_bone(context, deselect_all=not event.shift)


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos: Vector = rect.position
        size: Vector = rect.size

        # ol_color = self.outline_color
        # if (active or selected) and context.mode == 'POSE':
        #     ol_color = (1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)

        if self.use_ik_fk:
            ikfk_size = Vector((rect.dimensions[1], rect.dimensions[1]))
            ikfk_hovered = self.get_state('ik_fk_hovered', False)
            ikfk_pos = rect.get_point_relative(1.0, 0.0, apply_rotation=False)
            ikfk_state = self.get_ik_fk_state(context)

            draw.wg(
                self, 'IKFK_BASE',
                ikfk_pos, ikfk_size, rect.rotation,
                origin=Vector(rect.origin),
                roundness=1, # if ikfk_hovered else self.roundness,
                outline_thickness=1.5,
                bg_color=(.05, .05, .05, .95) if ikfk_hovered else (.05, .05, .05, .8),
            )

            ikfk_pos = get_center(ikfk_pos, ikfk_size)
            # rotate_point(ikfk_pos, rect.bottom_left, rect.rotation)
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
            roundness=self.roundness,
            outline_thickness=self.outline_thickness,
            bg_color=self.color if not hovered else Vector(self.color) * 1.2, # STYLE.
            # ol_color=ol_color
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
                color=self.text_color,
                origin=Vector(rect.origin)
            )

    def draw__edit(self, context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            if self.use_image and self.image is not None:
                return
            draw.box(
                self, 'BUTTON_BOX_ACTIVE',
                line_thickness=2 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
            )

    def draw__pose(self, context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active:
            if self.use_image and self.image is not None:
                return
            draw.box(
                self, 'BUTTON_BOX_ACTIVE',
                line_thickness=(1.5 * scale),
                color=(1.0, 1.0, .1, 1.0)
            )

    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        row = layout.row()
        row.enabled = not self.use_image
        row.prop(self, 'fit_to_text')

        layout.separator()

        layout.row().prop(rect_transform, 'origin')
        layout.row().prop(rect_transform, 'pivot')
        _sub = layout.column()
        _sub.enabled = not self.fit_to_text
        if self.fit_to_text and not self.use_image:
            _sub.row().prop(rect_transform, 'dimensions', text='Size')
        else:
            _sub.row().prop(rect_transform, 'edit_dimensions', text='Size')
        layout.prop(rect_transform, 'rotation')

        layout.prop(self, 'draw_depth')
