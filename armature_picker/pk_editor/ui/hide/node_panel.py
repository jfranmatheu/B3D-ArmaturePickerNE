from bl_ui.space_node import NODE_PT_active_node_generic, NODE_PT_active_node_color
# from bl_ui.properties_grease_pencil_common import AnnotationDataPanel
from bpy.types import NODE_PT_annotation, NODE_PT_active_node_properties

from armature_picker.pk_editor.poll import poll_picker_editor
from armature_picker.ackit import ACK


def register():
    ACK.Helper.UI_HIDE(NODE_PT_active_node_generic, poll_picker_editor)
    ACK.Helper.UI_HIDE(NODE_PT_active_node_properties, poll_picker_editor)
    ACK.Helper.UI_HIDE(NODE_PT_annotation, poll_picker_editor)
