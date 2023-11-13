from bpy.types import Context, Operator

from armature_picker.utils.node_editor import center_node_editor_view
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn


class AP_OT_center_view(Operator):
    bl_idname = 'armature_picker.center_view'
    bl_label = 'Center View'
    bl_description = "Center Armature Picker View"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=False)

    def execute(self, context: Context) -> OpsReturn:
        center_node_editor_view(context)
        return OpsReturn.FINISH
