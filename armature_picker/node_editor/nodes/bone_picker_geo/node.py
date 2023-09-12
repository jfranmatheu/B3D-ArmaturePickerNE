from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .._bone_picker_common import APNODE_BonePicker_Common

from .node_props import APNODE_BonePickerGeo_NodeProps
from .style_props import APNODE_BonePickerGeo_StyleProps

from bpy.types import Context, Armature, Bone, Event, UILayout, Object, Mesh
from mathutils import Vector, Matrix
import gpu

import numpy as np

from ....gpu import draw, draw_geo
from ....utils.geometry import rotate_point, point_inside_rect, get_center
from ....utils.armature import deselect_all_bones_from_active



class APNODE_BonePickerGeo(APNODE_BonePickerGeo_NodeProps, APNODE_BonePickerGeo_StyleProps, APNODE_BonePicker_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker_geo'
    bl_label = 'Bone Picker Geo'
    bl_icon = 'CONSTRAINT_BONE'


    def init(self, context):
        super().init(context)

        self.dirty_geo = True


    @property
    def dirty_geo(self) -> bool:
        return self.get_state('dirty_geo', False)

    @dirty_geo.setter
    def dirty_geo(self, state: bool) -> bool:
        self.set_state('dirty_geo', state)


    # ----- ON HOVER --------------------------------

    def on_hover(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
            # CHECK point_inside_circle with center in rect.origin and the user specified radius (a default of over 12).
            if self.geo_precision == 'FAST':
                return True
            if geo := draw_geo.Geometry.get(self, safe_context=False):
                return geo.on_hover(view_loc)
        return False


    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos: Vector = rect.position
        size: Vector = rect.size

        if self.object is not None and (geo := draw_geo.Geometry.get(self)) is not None:
            geo.draw(self)
        else:
            draw.rectangle(
                self, 'NO_OBJECT',
                color=(1.0, 0.0, 1.0, 1.0)
            )

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



    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin')
        layout.prop(self, 'geo_scale')
        layout.separator()
        layout.prop(self, 'draw_depth')
