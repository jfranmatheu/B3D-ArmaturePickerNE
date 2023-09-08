from bpy.types import PropertyGroup, NodeTree
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty

from .update import update_active_layer


class PG_PickerLayer(PropertyGroup):
    name: str # Internal name... Used as UUID.

    @property
    def uuid(self) -> str:
        return self.name

    enabled: BoolProperty(default=True, name="Visible", description="Show the picker elements inside this layer")
    edit_name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")


def register():
    NodeTree.active_picker_layer = IntProperty(default=-1, name="Active Picker Layer", update=lambda node_tree, ctx: update_active_layer(node_tree, ctx, node_tree.active_picker_layer))
    NodeTree.picker_layers = CollectionProperty(type=PG_PickerLayer)


# def unregister():
#     del NodeTree.picker_layers
