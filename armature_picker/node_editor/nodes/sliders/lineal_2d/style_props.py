from bpy.types import Context, UILayout, Image
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty


class APNODE_Slider2D_StyleProps:
    handle_scale: FloatProperty(
        name="Handle Scale",
        default=1.0,
        min=0.1,
        max=10,
        update=lambda node, ctx: node.set_state('dirty_handle_pos', True)
    )

    # STYLE PROPERTIES
    # ----------------------------------------------------------------
    
    
    def draw_styles(self, layout: UILayout) -> None:
        col = layout.column()
        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')
        col.prop(self, 'handle_scale')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'handle_color')
