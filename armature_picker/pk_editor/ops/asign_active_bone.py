from bpy.types import Context

from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn
from armature_picker.pk_editor.widgets._bone_picker_common import APNODE_BonePicker_Common


class AsignActiveBoneToBonePicker(ACK.Type.OPS.ACTION):
    label = 'Asign Active Bone'
    tooltip = "Asign active Bone to active BonePicker"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=True, use_picker_editor=True, use_active_node=(APNODE_BonePicker_Common,), use_active_bone=True)

    def action(self, context: Context) -> None:
        context.space_data.node_tree.nodes.active.bone_name = context.active_object.data.bones.active.name
