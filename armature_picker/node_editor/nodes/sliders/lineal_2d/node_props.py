from bpy.types import Context, UILayout, PropertyGroup
from bpy.props import PointerProperty

from .....utils.ui_layout import draw_section
from ..._slider_common import APNODE_Slider_DataConstraintsProps, RectTransform


class Axis(APNODE_Slider_DataConstraintsProps, PropertyGroup):
    pass


class APNODE_Slider2D_NodeProps:
    x_axis: PointerProperty(name="X Axis", type=Axis)
    y_axis: PointerProperty(name="Y Axis", type=Axis)
    
    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        self.x_axis.draw_slider_constraints_props(draw_section(layout, "X Axis"))
        self.y_axis.draw_slider_constraints_props(draw_section(layout, "Y Axis"))

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        # Draw data_path property field...
        pass

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        self.x_axis.draw_ui__edit(context, draw_section(layout, "X Axis"))
        self.y_axis.draw_ui__edit(context, draw_section(layout, "Y Axis"))

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin')
        layout.prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'dimensions')
        layout.prop(rect_transform, 'rotation')
        layout.prop(self, 'draw_depth')
