from armature_picker.ackit import Register

from bpy.types import LayerObjects, Context, Object, Mesh


last_mesh_id: int = 0


@Register.RNA_SUB(LayerObjects, 'active', persistent=True, data_path='view_layer.objects')
def on_active_object_change(context: Context, view_layer_objects: LayerObjects, active_object: Object):
    if active_object.type != 'MESH':
        return

    act_mesh: Mesh = active_object.data

    global last_mesh_id
    act_mesh_id = act_mesh.as_pointer()
    if last_mesh_id != act_mesh_id:
        last_mesh_id = act_mesh_id
