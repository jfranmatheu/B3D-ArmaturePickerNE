from bpy.types import Armature, NodeTree

from armature_picker.ackit import ACK


ACK.Helper.PROP(Armature, 'picker', ACK.Prop.POINTER.CUSTOM('Armature Picker', NodeTree, poll=lambda arm, node_tree: node_tree.bl_idname == 'AP_NODETREE'))
