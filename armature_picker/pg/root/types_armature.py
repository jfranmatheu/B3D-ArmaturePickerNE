from bpy.types import Armature, NodeTree
from bpy.props import PointerProperty


def register():
    Armature.picker = PointerProperty(name="Armature Picker", type=NodeTree, poll=lambda arm, node_tree: node_tree.bl_idname == 'AP_NODETREE')

def unregister():
    del Armature.picker
