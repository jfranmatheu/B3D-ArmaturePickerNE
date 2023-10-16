from bpy.types import Context, Operator

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn
from armature_picker.node_editor.nodes._bone_picker_common import APNODE_BonePicker_Common


class AP_OT_asign_active_bone(Operator):
    bl_idname = 'armature_picker.asign_active_bone'
    bl_label = 'Asign Active Bone'
    bl_description = "Asign active Bone to active BonePicker"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=True, use_picker_editor=True, use_active_node=(APNODE_BonePicker_Common,))

    def execute(self, context: Context) -> OpsReturn:
        if active_bone := context.object.data.bones.active:
            node = context.space_data.node_tree.nodes.active
            node.bone_name = active_bone.name
        return OpsReturn.FINISH
