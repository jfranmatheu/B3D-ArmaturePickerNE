from bpy.types import PropertyGroup, NodeTree, Context
from bpy.props import BoolProperty, StringProperty


class PG_PickerLayer(PropertyGroup):
    uuid: StringProperty(default="", name="Layer ID", description="Layer unique Identifier")

    def update_nodes_visibility(self, context: Context, nodes, layer_id: str, visible: bool) -> None:
        for node in nodes:
            if layer_id == node.picker_layer:
                node.visible = visible

    enabled: BoolProperty(default=True, name="Visible", description="Show the picker elements inside this layer",
                          update=lambda self, ctx: self.update_nodes_visibility(ctx, ctx.space_data.node_tree.nodes, self.uuid, self.enabled))
    name: StringProperty(default="Layer", name="Layer Name", description="Name of the layer")
