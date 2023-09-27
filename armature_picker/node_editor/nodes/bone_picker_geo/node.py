from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .._bone_picker_common import APNODE_BonePicker_Common

from .node_props import APNODE_BonePickerGeo_NodeProps, BonePickerGeo_Style

from bpy.types import Context, Armature, Bone, Event, UILayout, Object, Mesh
from mathutils import Vector

from ....gpu import draw, draw_geo
from ....utils.geometry import point_inside_rect, get_center, point_inside_circle



class APNODE_BonePickerGeo(APNODE_BonePickerGeo_NodeProps, APNODE_BonePicker_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker_geo'
    bl_label = 'Bone Picker Geo'
    bl_icon = 'CONSTRAINT_BONE'
    wg_type = 'bone_picker_geo'


    def init(self, context):
        super().init(context)

        self.dirty_geo = True
        self.use_override_theme = True


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
            if self.use_ik_fk and point_inside_circle(view_loc, Vector(rect.origin), self.ik_fk_size * 0.5):
                self.set_state('ik_fk_hovered', True)
                return True
            self.set_state('ik_fk_hovered', False)
            if self.geo_precision == 'FAST':
                return True
            if geo := draw_geo.Geometry.get(self, safe_context=False):
                return geo.on_hover(view_loc)
        return False


    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, style: BonePickerGeo_Style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        geo = draw_geo.Geometry.get(self)
        if geo is None:
            draw.rectangle_ui(
                self, 'NO_OBJECT',
                color=(1.0, 0.0, 1.0, 1.0) if hovered else (1, .4, .0, 1.0),
            )
            return

        if self.object is not None:
            if style.display_on_hover_only and not hovered and self.node_tree.picker_mode in {'POSE'}:
                pass
            else:
                geo.draw(self, hovered=hovered)


        if self.use_ik_fk and geo:
            ikfk_size = Vector((self.ik_fk_size, self.ik_fk_size))
            ikfk_hovered = self.get_state('ik_fk_hovered', False)
            ikfk_pos = Vector(rect.origin) - ikfk_size * 0.5
            ikfk_state = self.get_ik_fk_state(context)

            draw.wg(
                self, 'IKFK_BASE',
                ikfk_pos, ikfk_size, 0,
                roundness=1, # if ikfk_hovered else self.roundness,
                outline_thickness=1.5,
                bg_color=(.1, .1, .1, .9) if ikfk_hovered else (.05, .05, .05, .8),
            )

            ikfk_pos = get_center(ikfk_pos, ikfk_size)
            ikfk_size *= 0.5

            draw.wg(
                self, 'IKFK_TOGGLE',
                ikfk_pos-ikfk_size*0.5, ikfk_size, 0,
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
