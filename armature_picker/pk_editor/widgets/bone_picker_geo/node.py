from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .._bone_picker_common import APNODE_BonePicker_Common

from .node_props import APNODE_BonePickerGeo_NodeProps, PG__BonePickerGeo__LocalStyle, PG__BonePickerGeo__Style, PG_BonePickerGeo_Settings

from bpy.types import Context, UILayout
from mathutils import Vector

from ....gpu import draw
from armature_picker.pk_editor.widgets.bone_picker_geo.geometry import AP_PG_Geometry
from ....utils.geometry import point_inside_rect, get_center, point_inside_circle



class APNODE_BonePickerGeo(APNODE_BonePickerGeo_NodeProps, APNODE_BonePicker_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker_geo'
    bl_label = 'Bone Picker Geo'
    bl_description = 'Bone Picker Button with Custom Shape based on a geometry/Mesh Object\nMesh Object should be created in XY plane with no Z dimension'
    bl_icon = 'CONSTRAINT_BONE'
    wg_type = 'bone_picker_geo'


    def init(self, context):
        super().init(context)

        self.dirty = True
        self.use_override_theme = True
        self.geometry.init()

    @property
    def dirty_geo(self) -> bool:
        return self.get_state('dirty_geo', False)

    @dirty_geo.setter
    def dirty_geo(self, state: bool) -> bool:
        self.set_state('dirty_geo', state)


    # ----- ON HOVER --------------------------------

    def on_hover__pose(self, context: Context, rect: RectTransform, view_loc: Vector, _view_zoom: float) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation):
            # CHECK point_inside_circle with center in rect.origin and the user specified radius (a default of over 12).
            if self.use_ik_fk and point_inside_circle(view_loc, Vector(rect.origin), self.ik_fk_size * 0.5):
                self.set_state('ik_fk_hovered', True)
                return True
            self.set_state('ik_fk_hovered', False)
            return self.geometry.on_hover(self, view_loc)
        return False

    def on_hover__edit(self, context: Context, is_active: bool, rect: RectTransform, view_loc: Vector, view_zoom: float) -> bool:
        if super().on_hover__edit(context, is_active, rect, view_loc, view_zoom):
            return self.geometry.on_hover(self, view_loc, force_convex_hull=True)
        return False

    def test_borders(self, context: Context, rect: RectTransform, view_loc: Vector, view_zoom: float) -> bool:
        return False

    # ----- INVOKE --------------------------------


    # ----- DRAWING --------------------------------
    def draw_sel_cage(self, color: tuple, cage_thickness: float = 2) -> None:
        geo: AP_PG_Geometry = self.geometry
        geo.draw_outline(self, color=color, line_thickness=cage_thickness)

    def draw_redimension_handles(self, context: Context, view_loc: Vector, scale: float) -> None:
        pass

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, theme_style: PG__BonePickerGeo__Style, wg_settings: PG_BonePickerGeo_Settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        local_style: PG__BonePickerGeo__LocalStyle = self.style
        geo: AP_PG_Geometry = self.geometry

        if wg_settings.display_on_hover_only and not hovered and self.node_tree.picker_mode in {'POSE'}:
            pass
        else:
            if local_style.use_object_color:
                color = geo.color
            else:
                color = local_style.get_color(theme_style)
            geo.draw(self, color=color, hovered=hovered)
            if selected:
                if self.locked:
                    color = (.5, .5, .5, .5)
                else:
                    color = (1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
                self.draw_sel_cage(color, 2.0 * scale)

        if self.use_ik_fk:
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
