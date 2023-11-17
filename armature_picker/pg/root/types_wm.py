from armature_picker.ackit import ACK


@ACK.Deco.PROP_GROUP.ROOT.WINDOW_MANAGER('armature_picker')
class WM_PG_armature_picker:
    active_tool: ACK.Prop.ENUM(
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
