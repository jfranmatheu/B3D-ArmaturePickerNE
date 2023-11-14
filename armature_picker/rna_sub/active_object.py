from armature_picker.ackit import ACK
from armature_picker.utils.node_editor import get_armature_picker_editor
from armature_picker.pk_editor.node_tree import ensure_nodes_cache

import bpy
from bpy.types import Event, LayerObjects, Context, Object, Armature, Operator, SpaceNodeEditor


last_armature_id: int = 0
mouse_pos: tuple[int, int] = (0, 0)


class HACK_OT_get_mouse_pos(Operator):
    bl_idname = 'hack.get_mouse_pos'
    bl_label = "Get Mouse Position"

    def invoke(self, context: Context, event: Event):
        global mouse_pos
        mouse_pos = event.mouse_x, event.mouse_y
        return {'FINISHED'}


@ACK.Deco.RNA_SUB(LayerObjects, 'active', persistent=True, data_path='view_layer.objects')
def on_active_object_change(context: Context, view_layer_objects: LayerObjects, active_object: Object):
    if active_object is None or active_object.type != 'ARMATURE':
        return

    print(f"RNA::on_active_object_change -> {active_object.name}")

    act_armature: Armature = active_object.data

    # print("Change active object!", active_object)

    global last_armature_id
    act_armature_id = act_armature.as_pointer()
    if last_armature_id != act_armature_id:
        last_armature_id = act_armature_id
        picker = act_armature.picker
        if area := get_armature_picker_editor(context, ret_area=True):
            area.tag_redraw()
            area.spaces[0].node_tree = picker

            if picker is not None:
                ensure_nodes_cache(picker)
