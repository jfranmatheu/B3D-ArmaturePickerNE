from armature_picker.ackit import Register
from armature_picker.utils.node_editor import get_armature_picker_editor
from armature_picker.pk_editor.node_tree import ensure_nodes_cache

from bpy.types import Context, Object


@Register.RNA_SUB(Object, 'mode', persistent=True)
def on_mode_change(context: Context, object: Object, mode: str):
    if object.type != 'ARMATURE':
        return

    print(f"RNA::on_mode_change -> {mode} ['{object.name}']")

    if object.mode != 'POSE':
        return

    if picker := object.data.picker:
        if area := get_armature_picker_editor(context, ret_area=True):
            area.tag_redraw()
            for region in area.regions:
                region.tag_redraw()
            if area.spaces[0].node_tree != picker:
                area.spaces[0].node_tree = picker
            ensure_nodes_cache(picker)
