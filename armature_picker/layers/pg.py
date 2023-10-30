from bpy.types import PropertyGroup, NodeTree, Context
from bpy.props import BoolProperty, StringProperty


class PG_PickerLayer(PropertyGroup):
    uuid: StringProperty(default="", name="Layer ID", description="Layer unique Identifier")
    name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")
