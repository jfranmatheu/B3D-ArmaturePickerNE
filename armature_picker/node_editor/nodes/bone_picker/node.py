from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .._bone_picker_common import APNODE_BonePicker_Common
from .node_props import APNODE_BonePicker_NodeProps, BonePicker_Style

import bpy
from bpy.types import Context
from mathutils import Vector

from ....gpu import draw
from ....utils.geometry import get_center, point_inside_circle
from armature_picker.paths import Paths



class APNODE_BonePicker(APNODE_BonePicker_NodeProps, APNODE_BonePicker_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker'
    bl_label = 'Bone Picker'
    bl_description = 'Bone Picker Button'
    bl_icon = 'CONSTRAINT_BONE'
    wg_type = 'bone_picker'
    
    
    # ----- INIT PRESETS CONFIG --------------------------------
    
    def init_preset_image(self, context: Context) -> None:
        self.use_image = True
        self.keep_aspect_ratio = True
        self.node_tree.nodes.active = self
        # bpy.ops.armature_picker.load_image_for_active_node('INVOKE_DEFAULT')
        image = bpy.data.images.load(Paths.LIB_IMAGES('default_button_image.png'), check_existing=True)
        if not image.name.startswith('.'):
            image.name = '.default_button_image'
        self.image = image
        self.image_scale_x = 0.5

    # --------------------------------


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

    def on_hover__pose(self, context: Context, rect: RectTransform, view_loc: Vector, view_zoom: float) -> bool:
        if super().on_hover__pose(context, rect, view_loc, view_zoom):
            self.set_state('ik_fk_hovered', False)
            return True
        elif self.use_ik_fk:
            ikfk_pos, ikfk_size = self.get_ikfk_pos_size(center=True)
            if point_inside_circle(view_loc, ikfk_pos, ikfk_size.x * 0.5):
                self.set_state('ik_fk_hovered', True)
                return True
        return False


    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: BonePicker_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
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

        super().draw_common(context, view_loc, rect, style, wg_settings, scale, active, selected, hovered)
