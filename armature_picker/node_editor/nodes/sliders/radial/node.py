from armature_picker.utils.event import Mouse
from ..._base import AP_Node, Node
from ..._transform_props import RectTransform
from ..._slider_common import APNODE_Slider_Common
from .node_props import APNODE_SliderRadial_NodeProps, SliderRadial_Style

from bpy.types import Context, Event, UILayout
from mathutils import Vector

from math import degrees

from .....gpu import draw
from .....utils.geometry import point_inside_circle, rotate_point
from .....utils.math import map_value, clamp
from .....utils.operator import OpsReturn


text_size_for_20rad_and_3char_and_02thickness = 12



class APNODE_SliderRadial(APNODE_SliderRadial_NodeProps, APNODE_Slider_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_slider_radial'
    bl_label = 'Slider Radial'
    bl_icon = 'PROPERTIES'
    wg_type = 'slider_radial'


    def init(self, context):
        super().init(context)

        # Force an update. Respect the 1:1 dimensions.
        self.slider_radius = self.slider_radius
        # self.rect_transform.rotation = - pi / 2 # 90º


    # ----- ON HOVER --------------------------------

    def on_hover(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_circle(view_loc, Vector(rect.origin), rect.dimensions[0] * 0.5):
            return True
        return False


    # ----- MODAL --------------------------------

    def modal__pose(self, context: Context, event: Event, mouse: Mouse) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return 0

        if mouse.dir.x == 0:
            return 1

        delta_mouse_x = mouse.delta.x

        min_val, max_val = self.range
        range_val = max_val - min_val
        inc = range_val / 360

        # print(self.value, range_val)

        value = clamp(self.value + delta_mouse_x * inc * self.sensitivity, *self.range)

        # print("Relative Mouse Position:", rel_mouse, " ---> ", value)
        if value == self.value:
            return 1

        self.set_value(context, value)
        self.value = value
        self.update_handle_pos(context)
        self.dirty_label = True
        return 1


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, style: SliderRadial_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:

        value = self.get_value(context)
        if value is None:
            factor = 0
        else:
            factor = map_value(value, self.range, (0, 1))

        draw.wg_sld_rng_ui(
            self, 'SLIDER',
            factor=factor,
            arc_angle=style.bar_arc_angle,
            thickness_factor=style.u_thickness,
            invert_angle=style.invert_fill_flow,
            bg_color=style.color if not hovered else Vector(style.color) * 1.2,
            fill_color=style.fill_color if not hovered else Vector(style.fill_color) * 1.2,
        )

        if self.show_text_value:
            if self.unit_type == 'ANGLE' and value is not None:
                text = str(int(degrees(value)))
            else:
                text = str(round(value, 1)) if value is not None else 'NONE'
            text_dim = draw.get_text_dim(text, 12)
            w = style.u_thickness * rect.dimensions[0] - 8
            tw = text_dim[0]

            ts = w / tw * 12

            label_dimensions = Vector(text_dim)
            add_dim = Vector((label_dimensions.x * 0.25, label_dimensions.y * 0.1))
            label_dimensions += add_dim
            pivot = (0.5, 0.5)
            tex_pos = Vector(rect.origin) - label_dimensions * 0.5

            draw.text_cached(
                self.uuid, 'LABEL', self.dirty, self.dirty_label,
                tex_pos,
                Vector(rect.origin),
                text,
                ts,
                label_dimensions,
                pivot=pivot,
                angle=0,
                color=(.92, .92, .92, 1.0),
                origin=Vector(rect.origin)
            )


    def draw__edit(self, context, rect: RectTransform, style: SliderRadial_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        ''' Specific drawing for EDIT mode. '''
        if active or selected:
            if self.locked:
                color = (.5, .5, .5, .5)
            else:
                color = (1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
            draw.circle_ui(
                self, # 'SELECT_CAGE',
                margin=4,
                line_thickness=2 * scale,
                color=color
            )
