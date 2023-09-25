from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, EnumProperty

from ._base import StyleBase, use_active_node

    
class PG_ArmaturePickerTheme__Slider2D(StyleBase, PropertyGroup):
    @use_active_node
    def update_handle_scale(node, _context: Context) -> None:
        node.set_state('dirty_handle_pos', True)

    color: FloatVectorProperty(
        name="Color",
        description="Slider base color",
        default=(0.212, 0.63, 1.0, 0.9),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    handle_scale: FloatProperty(
        name="Handle Scale",
        default=0.75,
        min=0.1,
        max=10,
        update=update_handle_scale
    )

    handle_color: FloatVectorProperty(
        name="Handle Color",
        description="Slider handle color",
        default=(.95, .9, .84, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    roundness: FloatProperty(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=0.25,
        precision=2
    )

    outline_thickness: FloatProperty(
        name="Outline Thickness",
        description="Ouline thickness of the button",
        min=0,
        max=20,
        default=0.5,
        precision=1
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        col = layout.column()
        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')
        col.prop(self, 'handle_scale')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'handle_color')
