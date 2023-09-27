import bpy
from bpy.types import Context

from armature_picker.ackit import Register


@Register.HANDLER.LOAD_POST(persistent=True)
def on_load_post(context: Context, *any_dummy_args):
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname not in {'AP_NODETREE'}:
            continue
        if node_group.name.startswith('.'):
            continue
        node_group.reset()

    from ..node_editor.node_tree import reset_globals
    reset_globals()
