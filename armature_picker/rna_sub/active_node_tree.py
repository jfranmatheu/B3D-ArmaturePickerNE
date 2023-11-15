from armature_picker.ackit import ACK
from armature_picker.utils.node_editor import get_armature_picker_editor
from armature_picker.pk_editor.node_tree import ensure_nodes_cache

from bpy.types import Context, SpaceNodeEditor, NodeTree

from uuid import uuid4


@ACK.Deco.RNA_SUB(SpaceNodeEditor, 'node_tree', data_path='space_data', persistent=True)
def on_node_tree_change(context: Context, space_data: SpaceNodeEditor, node_tree: NodeTree):
    if space_data is None:
        space_data = get_armature_picker_editor(context)
        if space_data is None:
            return
        node_tree = space_data.node_tree
    if space_data.tree_type != 'AP_NODETREE':
        return
    if node_tree is None:
        return
    if context.active_object is None or context.active_object.type not in {'ARMATURE'}:
        return

    print(f"RNA::on_node_tree_change -> {node_tree.name}")

    if node_tree.uuid == '':
        # New NodeTree.
        node_tree.name = 'Picker'
        node_tree.uuid = uuid4().hex
        node_tree.new_layer(name='Layer')
    armature = context.active_object.data
    if armature.picker is None:
        armature.picker = node_tree
    ensure_nodes_cache(node_tree)
    node_tree.prepare_if_linked()

    node_tree.picker_update_flags.add('CENTER_VIEW')
