from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_picker_editor


try:
    from bl_ui.space_node import NODE_PT_node_tree_interface_inputs, NODE_PT_node_tree_interface_outputs

    def register():
        ACK.Helper.UI_HIDE(NODE_PT_node_tree_interface_inputs, poll_picker_editor)
        ACK.Helper.UI_HIDE(NODE_PT_node_tree_interface_outputs, poll_picker_editor)

except ImportError as e:
    # Blender 4.0 or greater.
    from bl_ui.space_node import NODE_PT_node_tree_interface
    
    def register():
        ACK.Helper.UI_HIDE(NODE_PT_node_tree_interface, poll_picker_editor)
