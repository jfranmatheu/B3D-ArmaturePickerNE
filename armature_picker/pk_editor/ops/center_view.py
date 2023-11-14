from bpy.types import Context

from armature_picker.ackit import ACK

from armature_picker.utils.node_editor import center_node_editor_view
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn



class CenterView(ACK.Type.OPS.ACTION):
    label = 'Center View'
    tooltip = "Center Armature Picker View"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=False)

    def action(self, context: Context) -> None:
        center_node_editor_view(context)
