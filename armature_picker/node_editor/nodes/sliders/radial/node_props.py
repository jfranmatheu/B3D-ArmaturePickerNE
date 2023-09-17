from bpy.types import Context, UILayout
from bpy.props import IntProperty, FloatProperty

from ..._transform_props import RectTransform


class APNODE_SliderRadial_NodeProps:
    ''' Transform. '''
    def update_dimensions(self, context: Context) -> None:
        size = self.slider_radius * 2
        self.rect_transform.dimensions = (size, size)


    slider_radius: IntProperty(
        name="Slider Radius",
        default=15,
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
        layout.prop(self, 'unit_type')
        if self.unit_type == 'VALUE':
            layout.prop(self, 'min_value')
            layout.prop(self, 'max_value')
        elif self.unit_type == 'ANGLE':
            layout.prop(self, 'min_angle')
            layout.prop(self, 'max_angle')

        layout.prop(self, 'sensitivity')
