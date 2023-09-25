from bpy.types import Context, UILayout
from bpy.props import IntProperty, FloatProperty, BoolProperty, PointerProperty

from ..._transform_props import RectTransform
from armature_picker.prefs.styles import SliderRadial_Style


class APNODE_SliderRadial_NodeProps:
    def get_style(self, theme) -> SliderRadial_Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=SliderRadial_Style)


    ''' Transform. '''
    def update_dimensions(self, context: Context) -> None:
        size = self.slider_radius * 2
        self.rect_transform.dimensions = (size, size)

    slider_radius: IntProperty(
        name="Slider Radius",
        default=20,
        min=10,
        max=256,
        update=update_dimensions
    )

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin')
        # layout.prop(rect_transform, 'pivot')
        layout.prop(self, 'slider_radius', text='Radius')
        layout.prop(rect_transform, 'rotation')
        layout.prop(self, 'draw_depth')


    ''' Constraints. '''
    sensitivity: FloatProperty(
        name="Sensitivity",
        default=2.0,
        min=0.1,
        max=10
    )

    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        col = layout.column(align=True)
        col.prop(self, 'unit_type')
        if self.unit_type == 'VALUE':
            col.prop(self, 'min_value')
            col.prop(self, 'max_value')
        elif self.unit_type == 'ANGLE':
            col.prop(self, 'min_angle')
            col.prop(self, 'max_angle')

        layout.prop(self, 'sensitivity')
