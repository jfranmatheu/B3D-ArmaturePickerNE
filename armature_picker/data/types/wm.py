from bpy.types import WindowManager, PropertyGroup
from bpy.props import PointerProperty, EnumProperty


class WM_PG_armature_picker(PropertyGroup):
    active_tool: EnumProperty(
        name="Active Tool",
        items=(
            ('SELECT', "Select & Control", "Pick bones and control sliders", 'RESTRICT_SELECT_OFF', 0),
            None,
            ('MOVE', "Move", "Move the bone", 'CON_LOCLIKE', 1),
            ('ROTATE', "Rotate", "Rotate the bone", 'CON_ROTLIKE', 2),
            ('SCALE', "Scale", "Scale the bone", 'CON_SIZELIKE', 3),
            ('GIMBALL', "Gimball", "Transform the bone as a gimball", 'ORIENTATION_GIMBAL', 4),
        ),
        default='SELECT',
    )


def register():
    WindowManager.armature_picker = PointerProperty(name="Armature Picker", type=WM_PG_armature_picker)

def unregister():
    del WindowManager.armature_picker
