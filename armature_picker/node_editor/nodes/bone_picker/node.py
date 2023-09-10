from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .node_props import APNODE_BonePicker_NodeProps
from .style_props import APNODE_BonePicker_StyleProps

import bpy
from bpy.types import Context, Armature, Bone, Event, UILayout
from mathutils import Vector

from ....gpu import draw
from ....utils.geometry import rotate_point, point_inside_rect, get_center
from ....utils.armature import deselect_all_bones_from_active



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
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation):
            self.set_state('ik_fk_hovered', False)
            return True
        elif self.use_ik_fk:
            size = Vector((rect.dimensions[1], 0)) + rect.size
            if point_inside_rect(view_loc, rect.bottom_left, size, rect.rotation):
                self.set_state('ik_fk_hovered', True)
                return True
        return False

    def on_hover_exit(self, context: Context | None = None) -> None:
        self.set_state('ik_fk_hovered', False)


    # ----- INVOKE --------------------------------

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            self.select_bone(context, deselect_all=not event.shift)
            self.select_node(context, deselect_all=not event.shift)

            if self.get_state('ik_fk_hovered'):
                self.toggle_ik_fk(context)


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos: Vector = rect.position
        size: Vector = rect.size

        # ol_color = self.outline_color
        # if (active or selected) and context.mode == 'POSE':
        #     ol_color = (1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)


        draw.wg(
            self, 'BUTTON_BASE',
            roundness=self.roundness,
            outline_thickness=self.outline_thickness,
            bg_color=self.color if not hovered else Vector(self.color) * 1.2, # STYLE.
            # ol_color=ol_color
        )

        if self.use_ik_fk:
            ikfk_pos = pos + Vector((size.x, 0))
            ikfk_size = Vector((rect.dimensions[1], rect.dimensions[1]))

            draw.rectangle(
                self, 'IKFK_BASE',
                color=(.05, .05, .05, .95) if self.get_state('ik_fk_hovered', False) else (.05, .05, .05, .8),
            )

            ikfk_pos = get_center(ikfk_pos, ikfk_size)
            text = '•' if self.get_ik_fk_state(context) else 'o'

            draw.text(
                ikfk_pos,
                text,
                self.text_size,
                pivot=(0.5, 0.5),
                color=(.92, .92, .92, 1)
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
            draw.box(
                self, 'BUTTON_BOX_ACTIVE',
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)
            )

    def draw__pose(self, context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            draw.box(
                self, 'BUTTON_BOX_ACTIVE',
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)
            )

    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.row().prop(rect_transform, 'origin')
        layout.row().prop(rect_transform, 'pivot')
        _sub = layout.column()
        _sub.enabled = not self.fit_to_text
        if self.fit_to_text:
            _sub.row().prop(rect_transform, 'dimensions', text='Size')
        else:
            _sub.row().prop(rect_transform, 'edit_dimensions', text='Size')
        layout.prop(rect_transform, 'rotation')
        
        layout.prop(self, 'draw_depth')
