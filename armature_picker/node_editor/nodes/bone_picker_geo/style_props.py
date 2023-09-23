from bpy.types import Context, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty


class APNODE_BonePickerGeo_StyleProps:

    # STYLE PROPERTIES
    # ----------------------------------------------------------------
    
    display_on_hover_only: BoolProperty(name="Show only on hover", description="(While in POSE mode) Display this element only when hovering over it", default=False)

    def draw_styles(self, layout: UILayout) -> None:
        layout.prop(self, 'display_on_hover_only')
        layout.prop(self, 'color')
