from bpy.types import PropertyGroup, NodeTree, Context, UILayout
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty
from mathutils import Vector

from armature_picker.gpu.draw import get_text_dim


COLORS = [
    Vector((225/255, 96/255, 91/255)),
    Vector((240/255, 162/255, 85/255)),
    Vector((240/255, 219/255, 85/255)),
    Vector((122/255, 203/255, 122/255)),
    Vector((93/255, 181/255, 233/255)),
    Vector((140/255, 89/255, 217/255)),
    Vector((197/255, 114/255, 183/255)),
    Vector((121/255, 84/255, 65/255)),
    Vector((72/255, 72/255, 72/255)) # Vector((95/255, 95/255, 95/255))
]
COLORS.reverse()

COLOR_ICONS = tuple(
    (f'SEQUENCE_COLOR_0{index_rev+1}', '', '', f'SEQUENCE_COLOR_0{index_rev+1}', index) for index, index_rev in enumerate(reversed(list(range(9))))
)


class PG_PickerLayer(PropertyGroup):
    label_dimensions: Vector = None

    def update_label_dimensions(self, context) -> None:
        self.label_dimensions = Vector(get_text_dim(self.name, 12))

    @property
    def color(self) -> tuple:
        for idx, ico in enumerate(COLOR_ICONS):
            if ico[0] == self.color_icon:
                return COLORS[idx]
        return (.06, .06, .06)

    uuid: StringProperty(default="", name="Layer ID", description="Layer unique Identifier")
    name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer", update=update_label_dimensions)
    use_pin: BoolProperty(default=True, name="Use Pin", description="Show a quick-access layer-toggle in the 2d Viewport\n(Will show up in POSE mode)")
    color_icon: EnumProperty(
        name="Color",
        description="This color will be used for the tab color (in case you pinned this layer)",
        items=COLOR_ICONS,
        default='SEQUENCE_COLOR_09',
    )

    view2d_box: FloatVectorProperty(default=(0, 0, 0, 0), size=4)
