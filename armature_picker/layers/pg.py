from bpy.types import PropertyGroup, NodeTree, Context
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty

from .update import update_active_layer


class PG_PickerLayer(PropertyGroup):
    name: str # Internal name... Used as UUID.

    @property
    def uuid(self) -> str:
        return self.name

    def update_nodes_visibility(self, context: Context, nodes, layer_id: str, visible: bool) -> None:
        for node in nodes:
            if visible:
                if layer_id in node.picker_layers:
                    node.visible = visible
            else:
                node.update_picker_layers(context)
        self.visible = False

    enabled: BoolProperty(default=True, name="Visible", description="Show the picker elements inside this layer",
                          update=lambda self, ctx: self.update_nodes_visibility(ctx, ctx.space_data.node_tree.nodes, self.uuid, self.enabled))
    edit_name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")


def register():
    NodeTree.active_picker_layer = IntProperty(default=-1, name="Active Picker Layer", update=lambda node_tree, ctx: update_active_layer(node_tree, ctx, node_tree.active_picker_layer))
    NodeTree.picker_layers = CollectionProperty(type=PG_PickerLayer)


# def unregister():
#     del NodeTree.picker_layers
