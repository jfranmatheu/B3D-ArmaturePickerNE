from mathutils import Vector

from armature_picker.gpu import draw
from armature_picker.pk_editor.widgets._transform_props import RectTransform
from armature_picker.utils.event import GEvent

from .._base import AP_Node, Context, Event, Node
from .node_props import APNODE_Toggle_NodeProps, PG__Toggle__Style


class APNODE_Toggle(APNODE_Toggle_NodeProps, AP_Node, Node):
    bl_idname = 'AP_NODE_toggle'
    bl_label = 'Toggle'
    bl_icon = 'DOT'
    wg_type = 'toggle'

    draw_layer: int = 15

    def init(self, context):
        super().init(context)

    def toggle(self, context: Context) -> None:
        value = context.path_resolve(self.data_path, coerce=True)
        if not isinstance(value, bool):
            return
        split = self.data_path.split('.')
        path = '.'.join(split[:-1])
        attr = split[-1]
        setattr(context.path_resolve(path), attr, not value)

    def get_toggle_state(self, context: Context) -> bool:
        value = context.path_resolve(self.data_path, coerce=True)
        if not isinstance(value, bool):
            return False
        return value


    def on_hover__pose(self, context: Context, rect: RectTransform, view_loc: Vector, _view_zoom: float) -> bool:
        res = super().on_hover__pose(context, rect, view_loc, _view_zoom)
        if res:
            context.region.tag_redraw()
        return res

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            self.toggle(context)
            context.region.tag_redraw()
            return {'FINISHED'}

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: PG__Toggle__Style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        print("drawing toggle", self)
        draw.wg_ui(
            self, 'TOGGLE_BASE',
            roundness=style.roundness,
            outline_thickness=1,
            bg_color=style.color if not hovered else Vector(style.color) * 1.2
        )

        color = style.toggle_color if self.get_toggle_state(context) else Vector(style.color) * 0.64

        pad = Vector((2, 2)) * scale
        draw.wg(
            self, 'TOGGLE_FILL',
            pos=rect.bottom_left + pad, size=rect.size - pad * 2, rotation=0,
            roundness=style.roundness,
            outline_thickness=0,
            bg_color=color if not hovered else Vector(color) * 1.2
        )

    def draw__pose(self, context: Context, view_loc: Vector, rect: RectTransform, style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if hovered:
            text_pos, text_dim = draw.text(
                view_loc.copy(),
                self.tooltip,
                int(12 * scale),
                (0.5, 0),
                alpha=0,
            )
            pad = Vector((2, 2)) * scale
            draw.rectangle(
                None, None,
                text_pos - pad, text_dim + pad * 2, 0, (.05, .05, .05, .92)
            )
            draw.text(
                view_loc.copy(),
                self.tooltip,
                int(12 * scale),
                (0.5, 0),
                use_shadow=True
            )
