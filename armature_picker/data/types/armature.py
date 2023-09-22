from bpy.types import Armature, NodeTree
from bpy.props import PointerProperty


def register():
    Armature.picker = PointerProperty(name="Armature Picker", type=NodeTree)

def unregister():
    del Armature.picker
