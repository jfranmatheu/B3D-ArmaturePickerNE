from armature_picker.ackit import Register
from armature_picker.utils.node_editor import get_armature_picker_editor

from bpy.types import Context, Object


@Register.RNA_SUB(Object, 'mode', persistent=True)
def on_mode_change(context: Context, object: Object, mode: str):
    # print(f"RNA::on_mode_change -> {mode} ['{object.name}']")
    if object.type != 'ARMATURE':
        return
    if object.mode != 'POSE':
        return
    
    if picker := object.data.picker:
        if area := get_armature_picker_editor(context, ret_area=True):
            area.tag_redraw()
            for region in area.regions:
                region.tag_redraw()
            if area.spaces[0].node_tree != picker:
                area.spaces[0].node_tree = picker
