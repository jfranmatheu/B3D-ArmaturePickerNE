from .._base import AP_Node, Node
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

    def on_hover(self, context: Context, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, self.position, self.size, self.rotation):
            self.set_state('ik_fk_hovered', False)
            return True
        elif self.use_ik_fk:
            size = Vector((self.dimensions[1], 0)) + self.size
            if point_inside_rect(view_loc, self.position, size, self.rotation):
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

    def draw_common(self, context: Context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos, size = self.position, self.size

        draw.rectangle(
            self.uuid, 'BUTTON_BASE', self.dirty, # CACHE.
            pos, size, self.rotation, # TRANSFORM.
            self.color if not hovered else Vector(self.color) * 0.8 # STYLE.
        )

        if self.use_ik_fk:
            ikfk_pos = pos + Vector((size.x, 0))
            ikfk_size = Vector((self.dimensions[1], self.dimensions[1]))

            draw.rectangle(
                self.uuid, 'IKFK_BASE', self.dirty, # CACHE.
                ikfk_pos, ikfk_size, self.rotation, # TRANSFORM.
                (.05, .05, .05, .95) if self.get_state('ik_fk_hovered', False) else (.05, .05, .05, .8),
                origin=self.origin
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
                tex_pos = self.position + Vector((padding, padding))
            else:
                align = self.text_alignment
                if align == 'LEFT':
                    pivot = (0.0, 0.5)
                elif align == 'CENTER':
                    pivot = (0.5, 0.5)
                elif align == 'RIGHT':
                    pivot = (1.0, 0.5)

                tex_pos = Vector((
                    self.position.x + size.x * pivot[0] - label_dimensions.x * pivot[0],
                    self.position.y + size.y * pivot[1] - label_dimensions.y * pivot[1],
                ))

            draw.text_cached(
                self.uuid, 'LABEL', self.dirty, self.dirty_label,
                tex_pos,
                Vector(self.origin) if self.rotation == 0 else rotate_point(pos + Vector((padding, padding)), self.origin, self.rotation),
                self.label,
                self.text_size,
                label_dimensions,
                pivot=pivot if self.rotation == 0 else (0, 0),
                angle=self.rotation,
                color=self.text_color
            )

    def draw__edit(self, context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            draw.box(
                self.uuid, 'BUTTON_BOX_ACTIVE', self.dirty,
                self.position, self.size, self.rotation,
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)
            )

    def draw__pose(self, context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active:
            draw.box(
                self.uuid, 'BUTTON_BOX_ACTIVE', self.dirty,
                self.position, self.size, self.rotation,
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0)
            )


    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout) -> None:
        layout.prop(self, 'origin')
        layout.prop(self, 'rotation')
        _sub = layout.column()
        _sub.enabled = not self.fit_to_text
        _sub.prop(self, 'scale')
        if self.fit_to_text:
            _sub.prop(self, 'dimensions')
        else:
            _sub.prop(self, 'edit_dimensions')
