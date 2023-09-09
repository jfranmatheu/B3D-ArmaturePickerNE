from .._base import AP_Node, Node
from .node_props import APNODE_BonePicker_NodeProps
from .style_props import APNODE_BonePicker_StyleProps

import bpy
from bpy.types import Context, Armature, Bone, Event, UILayout
from mathutils import Vector

from ....gpu import draw
from ....utils.geometry import rotate_point
from ....utils.armature import deselect_all_bones_from_active



class AP_BonePickerNode(APNODE_BonePicker_NodeProps, APNODE_BonePicker_StyleProps, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker'
    bl_label = 'Bone Picker'
    bl_icon = 'CONSTRAINT_BONE'

    draw_layer = 10


    # ----- SELECT METHODS --------------------------------

    def select_bone(self, context: Context, deselect_all: bool = True) -> None:
        armature: Armature = context.active_object.data
        bones = armature.bones
        bone: Bone
        if bone := bones.get(self.bone_name, None):
            if deselect_all:
                deselect_all_bones_from_active(context)
            bone.select = True
            bones.active = bone


    # ----- INVOKE --------------------------------

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.select_bone(context, deselect_all=not event.shift)
            self.select_node(context, deselect_all=not event.shift)


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos, size = self.position, self.size

        draw.rectangle(
            self.uuid, 'BUTTON_BASE', self.dirty, # CACHE.
            pos, size, self.rotation, # TRANSFORM.
            self.color if not hovered else Vector(self.color) * 0.8 # STYLE.
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
