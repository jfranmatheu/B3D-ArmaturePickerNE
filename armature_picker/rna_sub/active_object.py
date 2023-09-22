from armature_picker.ackit import Register
from armature_picker.utils.node_editor import get_armature_picker_editor

from bpy.types import LayerObjects, Context, Object, Armature


last_armature_id: int = 0


@Register.RNA_SUB(LayerObjects, 'active', persistent=True, data_path='view_layer.objects')
def on_active_object_change(context: Context, view_layer_objects: LayerObjects, active_object: Object):
    if active_object is None or active_object.type != 'ARMATURE':
        return

    act_armature: Armature = active_object.data

    global last_armature_id
    act_armature_id = act_armature.as_pointer()
    if last_armature_id != act_armature_id:
        last_armature_id = act_armature_id
        
        if picker := act_armature.picker:
            if node_editor := get_armature_picker_editor(context):
                node_editor.node_tree = picker
