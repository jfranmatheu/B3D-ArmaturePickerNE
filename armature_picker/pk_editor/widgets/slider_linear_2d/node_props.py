from bpy.types import Context, UILayout, PropertyGroup
from bpy.props import PointerProperty

from armature_picker.utils.ui_layout import draw_section
from armature_picker.pk_editor.widgets._slider_common import APNODE_Slider_DataConstraintsProps, RectTransform
from .wg_style import PG__Slider2D__Style


class Axis(APNODE_Slider_DataConstraintsProps, PropertyGroup):
    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        col = layout.column(align=True)
        col.prop(self, 'unit_type')
        if self.unit_type == 'VALUE':
            col.prop(self, 'min_value')
            col.prop(self, 'max_value')
        elif self.unit_type == 'ANGLE':
            col.prop(self, 'min_angle')
            col.prop(self, 'max_angle')



class APNODE_Slider2D_NodeProps:
    def get_style(self, theme) -> PG__Slider2D__Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=PG__Slider2D__Style)

    x_axis: PointerProperty(name="X Axis", type=Axis)
    y_axis: PointerProperty(name="Y Axis", type=Axis)

    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        self.x_axis.draw_slider_constraints_props(draw_section(layout, "X Axis"))
        self.y_axis.draw_slider_constraints_props(draw_section(layout, "Y Axis"))

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        # Draw data_path property field...
        pass

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        self.x_axis.draw_ui__edit(context, draw_section(layout, "X Axis"), dimension='x')
        self.y_axis.draw_ui__edit(context, draw_section(layout, "Y Axis"), dimension='y')

        if hasattr(self, 'show_text_value'):
            layout.separator()
            layout.prop(self, 'show_text_value')

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin')
        layout.prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'dimensions')
        layout.prop(rect_transform, 'rotation')
        layout.prop(self, 'draw_depth')
