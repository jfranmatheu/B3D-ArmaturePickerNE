from armature_picker.utils.event import Mouse
from ..._base import AP_Node, Node
from ..._transform_props import RectTransform
from ..._slider_common import APNODE_Slider_Common
from .node_props import APNODE_SliderRadial_NodeProps
from .style_props import APNODE_SliderRadial_StyleProps

from bpy.types import Context, Event, UILayout
from mathutils import Vector

from math import sin

from .....gpu import draw
from .....utils.geometry import get_center, angle_signed, angle_between, point_inside_circle
from .....utils.math import map_value
from .....utils.operator import OpsReturn




class APNODE_SliderRadial(APNODE_SliderRadial_NodeProps, APNODE_SliderRadial_StyleProps, APNODE_Slider_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_slider_radial'
    bl_label = 'Slider Radial'
    bl_icon = 'PROPERTIES'


    # ----- ON HOVER --------------------------------

    def on_hover(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_circle(view_loc, Vector(rect.origin), rect.dimensions[0]):
            return True
        return False


    # ----- MODAL --------------------------------

    def modal__pose(self, context: Context, event: Event, mouse: Mouse) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return 0

        if mouse.local_dir.x == 0:
            return OpsReturn.RUN

        if self.clamp_slider:
            rect: RectTransform = self.rect_transform
            rel_mouse = mouse.local_rel # rect.convert_abs_coord_to_rel_coord(mouse.current, context)

            value = map_value(rel_mouse.x, (0, 1), self.range)

            # print("Relative Mouse Position:", rel_mouse, " ---> ", value)
            if value == self.value:
                return 1
        else:
            value = self.value + mouse.delta.x * self.step

        self.set_value(context, value)
        self.value = value
        return 1


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.clamp_slider:
            value = self.get_value(context)
            if value is None:
                factor = 0
            else:
                factor = map_value(value, self.range, (0, 1))
        else:
            factor = 0

        draw.wg_sld_rng_ui(
            self, 'SLIDER',
            factor=factor,
            arc_angle=self.bar_arc_angle,
            thickness_factor=self.u_thickness,
            bg_color=self.color,
            fill_color=self.fill_color
        )

        return

        if self.clamp_slider and self.handle_type == 'CIRCLE':
            # Check which factor is the handle radius over the slider bar width.
            handle_rad_factor = (rect.dimensions[1] * 0.5) / rect.dimensions[0]
            factor = map_value(factor, (0, 1), (handle_rad_factor, 1 - handle_rad_factor))

        if self.bar_type == 'FILL':
            draw.wg_sld_ui(
                self, 'SLIDER',
                factor=factor,
                roundness=self.roundness,
                # outline_thickness=self.outline_thickness,
                bg_color=self.color if not hovered else Vector(self.color) * 1.2,
                fill_color=self.fill_color if not hovered else Vector(self.fill_color) * 1.2,
            )
        elif self.bar_type == 'LINE':
            pos = rect.get_point_relative(0, 0)
            size = Vector((rect.dimensions[0], self.bar_line_thickness * scale))
            pos.y += (rect.dimensions[1] * 0.5 - size.y * 0.5)
            draw.rectangle(
                self, 'SLIDER_LINE',
                pos, size, rect.rotation,
                # roundness=self.roundness,
                # outline_thickness=self.outline_thickness,
                color=self.color if not hovered else Vector(self.color) * 1.2,
                origin=Vector(rect.origin)
            )

        if self.clamp_slider:
            if self.handle_type == 'CIRCLE':
                handle_size = Vector((rect.dimensions[1], rect.dimensions[1])) # * 1.5
                roundness = self.roundness
                outline_thickness = 0.0 if self.bar_type == 'FILL' else self.outline_thickness

            elif self.handle_type == 'LINE':
                handle_size = Vector((2, rect.dimensions[1]))
                roundness = 0.2
                outline_thickness = 0.0

            handle_pos = rect.get_point_relative(factor, 0.5, apply_rotation=True, rotate_from_origin=True) # , apply_rotation=True, rotate_from_origin=True)
            handle_pos -= handle_size * 0.5 # get_center(handle_pos, handle_size)

            dirty_handle_pos = self.dirty_handle_pos
            draw.wg(
                self, 'SLIDER_HANDLE',
                handle_pos, handle_size, rect.rotation,
                roundness=roundness,
                outline_thickness=outline_thickness,
                bg_color=self.handle_color,
                # origin=Vector(rect.origin),
                dirty=dirty_handle_pos
            )

            if dirty_handle_pos:
                self.set_state('dirty_handle_pos', False)
