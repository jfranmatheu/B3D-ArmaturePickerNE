from bpy.types import PropertyGroup, NodeTree, Context
from bpy.props import BoolProperty, StringProperty
from mathutils import Vector

from armature_picker.gpu.draw import get_text_dim


class PG_PickerLayer(PropertyGroup):
    label_dimensions: Vector = None

    def update_label_dimensions(self, context) -> None:
        self.label_dimensions = Vector(get_text_dim(self.name, 12))

    uuid: StringProperty(default="", name="Layer ID", description="Layer unique Identifier")
    name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer", update=update_label_dimensions)
    use_pin: BoolProperty(default=True, name="Use Pin", description="Show a quick-access layer-toggle in the 2d Viewport\n(Will show up in POSE mode)")
