from bpy.types import Context, UILayout
from bpy.props import PointerProperty, BoolProperty

from armature_picker.prefs.styles import SliderLinear_Style


class APNODE_Slider_NodeProps:
    def get_style(self, theme) -> SliderLinear_Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=SliderLinear_Style)

    def update_handle_pos(self, context: Context):
        self.set_state('dirty_handle_pos', True)
        context.area.tag_redraw()           
