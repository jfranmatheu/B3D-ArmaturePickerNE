from armature_picker.utils.event import Mouse
from ..._base import AP_Node, Node
from ..._transform_props import RectTransform
from ..._slider_common import APNODE_Slider_CommonNode
from .node_props import APNODE_Slider2D_NodeProps, SliderLinear2D_Style

from bpy.types import Context, Event, UILayout
from mathutils import Vector

from .....gpu import draw
from .....utils.geometry import point_inside_rect, get_center
from .....utils.math import map_value
from .....utils.operator import OpsReturn




class APNODE_SliderLinear2D(APNODE_Slider2D_NodeProps, APNODE_Slider_CommonNode, AP_Node, Node):
    bl_idname = 'AP_NODE_slider_2d'
    bl_label = 'Slider 2D'
    bl_icon = 'PROPERTIES'
    wg_type = 'slider_linear_2d'

    default_width = 40
    default_height = 40


    def init(self, context):
        super().init(context)

        self.show_text_value = False

    def update_dimensions(self, context: Context) -> None:
        self.rect_transform.dimensions = self.rect_transform.edit_dimensions


    def update_handle_pos(self, context: Context) -> None:
        self.set_state('dirty_handle_pos', True)
        context.region.tag_redraw()


    def get_value(self, context: Context) -> tuple | None:
        x_value, y_value = self.x_axis.get_value(context), self.y_axis.get_value(context)
        if x_value is None or y_value is None:
            return None
        return (x_value, y_value)

    def set_value(self, context: Context, values: tuple) -> None:
        self.x_axis.set_value(context, values[0])
        self.y_axis.set_value(context, values[1])

        self.update_handle_pos(context)


    # ----- ON HOVER --------------------------------

    def on_hover__pose(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
            return True
        return False


    # ----- MODAL --------------------------------

    def modal__pose(self, context: Context, event: Event, mouse: Mouse) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return 0

        if mouse.local_dir.x == 0 and mouse.local_dir.y == 0:
            return OpsReturn.RUN

        rel_mouse = mouse.local_rel
        value_x = map_value(rel_mouse.x, (0, 1), self.x_axis.range)
        value_y = map_value(rel_mouse.y, (0, 1), self.y_axis.range)

        # print("Relative Mouse Position:", rel_mouse, " ---> ", value)
        if value_x == self.value[0] and value_y == self.value[1]:
            return 1

        values = (value_x, value_y)

        self.set_value(context, values)
        self.value = values
        return 1


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: SliderLinear2D_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:


        draw.wg_grid_ui(
            self, 'SLIDER_2D',
            roundness=style.roundness,
            outline_thickness=style.outline_thickness,
            bg_color=style.color if not hovered else Vector(style.color) * 1.2,
        )

        factor_x, factor_y = 0, 0

        values = self.get_value(context)
        if values is not None:
            factor_x = map_value(values[0], self.x_axis.range, (0, 1))
            factor_y = map_value(values[1], self.y_axis.range, (0, 1))

        # Check which factor is the handle radius over the slider bar width.
        handle_radius = 5 * scale * style.handle_scale
        handle_rad_factor_x = handle_radius / rect.dimensions[0]
        handle_rad_factor_y = handle_radius / rect.dimensions[1]
        factor_x = map_value(factor_x, (0, 1), (handle_rad_factor_x, 1 - handle_rad_factor_x))
        factor_y = map_value(factor_y, (0, 1), (handle_rad_factor_y, 1 - handle_rad_factor_y))

        handle_size = Vector((handle_radius, handle_radius)) * 2
        handle_pos = rect.get_point_relative(factor_x, factor_y, apply_rotation=True, rotate_from_origin=True)
        handle_pos -= handle_size * 0.5 # get_center(handle_pos, handle_size)

        dirty_handle_pos = self.dirty_handle_pos
        draw.wg(
            self, 'SLIDER_HANDLE',
            handle_pos, handle_size, rect.rotation,
            roundness=1.0,
            outline_thickness=1.0,
            bg_color=style.handle_color,
            # origin=Vector(rect.origin),
            dirty=dirty_handle_pos
        )

        if dirty_handle_pos:
            self.set_state('dirty_handle_pos', False)


    def modal_draw__pose(self, context: Context, rect: RectTransform, style: SliderLinear2D_Style, ui_scale: float) -> None:
        if not self.show_text_value:
            return

        values = self.get_value(context)
        if values is not None:
            value_x = round(values[0], 2) if isinstance(values[0], float) else values[0]
            value_y = round(values[1], 2) if isinstance(values[1], float) else values[1]

            text = f'X: {value_x},  Y: {value_y}'
        else:
            text = 'NONE'

        draw.text(
            rect.get_point_relative(0, 0, offset=Vector((0, -10))),
            text,
            10,
            (0, 1)
        )
