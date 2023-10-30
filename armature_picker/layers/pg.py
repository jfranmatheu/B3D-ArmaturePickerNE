from bpy.types import PropertyGroup, NodeTree, Context
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty

from .update import update_active_layer


class PG_PickerLayer(PropertyGroup):
    name: StringProperty() # Internal name... Used as UUID.

    @property
    def uuid(self) -> str:
        return self.name

    def update_nodes_visibility(self, context: Context, nodes, layer_id: str, visible: bool) -> None:
        for node in nodes:
            if layer_id == node.picker_layer:
                node.visible = visible

    enabled: BoolProperty(default=True, name="Visible", description="Show the picker elements inside this layer",
                          update=lambda self, ctx: self.update_nodes_visibility(ctx, ctx.space_data.node_tree.nodes, self.uuid, self.enabled))
    edit_name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")
