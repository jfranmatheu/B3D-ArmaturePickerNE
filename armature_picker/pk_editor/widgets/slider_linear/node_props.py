from bpy.types import Context, UILayout
from bpy.props import PointerProperty, BoolProperty

from .wg_style import PG__SliderLinear__Style


class APNODE_Slider_NodeProps:
    def get_style(self, theme) -> PG__SliderLinear__Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=PG__SliderLinear__Style)

    def update_handle_pos(self, context: Context):
        self.set_state('dirty_handle_pos', True)
        context.area.tag_redraw()           
