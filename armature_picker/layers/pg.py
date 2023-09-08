from bpy.types import PropertyGroup, NodeTree
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty


class PG_PickerLayer(PropertyGroup):
    enabled: BoolProperty(default=True, name="Visible", description="Show the picker elements inside this layer")
    name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")


def register():
    NodeTree.active_picker_layer = IntProperty(default=-1, name="Active Picker Layer")
    NodeTree.picker_layers = CollectionProperty(type=PG_PickerLayer)


# def unregister():
#     del NodeTree.picker_layers
