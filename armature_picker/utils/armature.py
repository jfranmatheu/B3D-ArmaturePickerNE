from bpy.types import Context, Bone


def deselect_all_bones_from_active(context: Context) -> None:
    if context.active_object is None:
        return
    if context.active_object.type != 'ARMATURE':
        return
    if context.mode == 'POSE':
        armature_bones: dict[str, Bone] = context.active_object.data.bones
        for bone in context.selected_pose_bones_from_active_object:
            armature_bones[bone.name].select = False
    else:
        for bone in context.selected_bones:
            bone.select = False
