from armature_picker.utils.event import Mouse
from ..._base import AP_Node, Node
from ..._transform_props import RectTransform
from ..._slider_common import APNODE_Slider_Common
from .node_props import APNODE_Slider_NodeProps, SliderLinear_Style

from bpy.types import Context, Event, UILayout
from mathutils import Vector

from .....gpu import draw
from .....utils.geometry import point_inside_rect
from .....utils.math import map_value
from .....utils.operator import OpsReturn



class APNODE_SliderLinear(APNODE_Slider_NodeProps, APNODE_Slider_Common, AP_Node, Node):
    bl_idname = 'AP_NODE_slider'
    bl_label = 'Slider'
    bl_icon = 'PROPERTIES'
    wg_type = 'slider_linear'

    default_width = 100
    default_height = 12



    def init(self, context):
        super().init(context)

        self.show_text_value = False


    # ----- ON HOVER --------------------------------

    def on_hover__pose(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        if point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation, origin=Vector(rect.origin)):
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
            rel_mouse = mouse.local_rel

            value = map_value(rel_mouse.x, (0, 1), self.range)

            # print("Relative Mouse Position:", rel_mouse, " ---> ", value)
            if value == self.value:
                return 1
        else:
            value = self.value + mouse.local_delta.x * self.step

        self.set_value(context, value)
        self.value = value
        self.update_handle_pos(context)
        return 1


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: SliderLinear_Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:

        if self.clamp_slider:
            value = self.get_value(context)
            if value is None:
                factor = 0
            else:
                factor = map_value(value, self.range, (0, 1))
        else:
            factor = 0

        if self.clamp_slider and style.handle_type == 'CIRCLE':
            # Check which factor is the handle radius over the slider bar width.
            handle_rad_factor = (rect.dimensions[1] * 0.5) / rect.dimensions[0]
            factor = map_value(factor, (0, 1), (handle_rad_factor, 1 - handle_rad_factor))

        if style.bar_type == 'FILL':
            draw.wg_sld_ui(
                self, 'SLIDER',
                factor=factor,
                roundness=style.roundness,
                # outline_thickness=style.outline_thickness,
                bg_color=style.color if not hovered else Vector(style.color) * 1.2,
                fill_color=style.fill_color if not hovered else Vector(style.fill_color) * 1.2,
            )
        elif style.bar_type == 'LINE':
            pos = rect.get_point_relative(0, 0)
            size = Vector((rect.dimensions[0], style.bar_line_thickness * scale))
            pos.y += (rect.dimensions[1] * 0.5 - size.y * 0.5)
            draw.rectangle(
                self, 'SLIDER_LINE',
                pos, size, rect.rotation,
                # roundness=style.roundness,
                # outline_thickness=style.outline_thickness,
                color=style.color if not hovered else Vector(style.color) * 1.2,
                origin=Vector(rect.origin)
            )

        if self.clamp_slider:
            if style.bar_type == 'FILL' and not style.show_handle:
                return

            if style.handle_type == 'CIRCLE':
                handle_size = Vector((rect.dimensions[1], rect.dimensions[1])) # * 1.5
                roundness = style.roundness
                outline_thickness = 0.0 if style.bar_type == 'FILL' else style.outline_thickness

            elif style.handle_type == 'LINE':
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
                bg_color=style.handle_color,
                # origin=Vector(rect.origin),
                dirty=dirty_handle_pos
            )

            if dirty_handle_pos:
                self.set_state('dirty_handle_pos', False)


    def modal_draw__pose(self, context: Context, rect: RectTransform, style: SliderLinear_Style, ui_scale: float) -> None:
        if not self.show_text_value:
            return
        if not self.in_modal:
            return

        if style.handle_type == 'CIRCLE':
            handle_size = Vector((rect.dimensions[1], rect.dimensions[1]))
        elif style.handle_type == 'LINE':
            handle_size = Vector((2, rect.dimensions[1]))

        value = self.get_value(context)
        if value is None:
            factor = 0
            text = 'NONE'
        else:
            factor = map_value(value, self.range, (0, 1))
            if isinstance(value, float):
                value = round(value, 3)
            text = str(value)

        if style.handle_type == 'CIRCLE':
            # Check which factor is the handle radius over the slider bar width.
            handle_rad_factor = (rect.dimensions[1] * 0.5) / rect.dimensions[0]
            factor = map_value(factor, (0, 1), (handle_rad_factor, 1 - handle_rad_factor))

        rect = self.rect_transform
        handle_pos = rect.get_point_relative(factor, 0.5, apply_rotation=True, rotate_from_origin=True)
        handle_pos -= handle_size * 0.5

        handle_pos.y += handle_size.y * 1.5

        draw.text(
            handle_pos,
            text,
            11,
            (0, 0),
            color=(.92, .92, .92, 1)
        )
