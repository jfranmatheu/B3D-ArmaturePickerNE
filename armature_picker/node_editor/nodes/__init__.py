from .bone_picker.node import AP_BonePickerNode
from .bone_picker_geo.node import APNODE_BonePickerGeo
from .image.node import APNODE_Image
from .label.node import APNODE_Label
from .sliders.linear.node import APNODE_SliderLinear
from .sliders.radial.node import APNODE_SliderRadial
from .sliders.linear_2d.node import APNODE_SliderLinear2D
from .button_script.node import APNODE_ButtonScript


NODES = (
    (
        {
            'name': 'Bone-Picker',
            'icon': 'CONSTRAINT_BONE',
            'items': (
                (AP_BonePickerNode, 'Button', 'SEQ_SEQUENCER'),
                (AP_BonePickerNode.bl_idname + '@' + 'init_preset_image', 'Button Image', 'IMAGE_PLANE'),
                (APNODE_BonePickerGeo, 'Geometry Shape', 'MESH_MONKEY'),
            )
        },
        {
            'name': 'Action Buttons',
            'icon': 'FILE_SCRIPT',
            'items': (
                (APNODE_ButtonScript, 'Custom Script', 'TEXT'),
            )
        },
    ),
    {
        'name': 'Sliders',
        'icon': 'PROPERTIES',
        'items': (
            (APNODE_SliderLinear, 'Lineal', 'OPTIONS'),
            (APNODE_SliderRadial, 'Radial', 'ANTIALIASED'),
            (APNODE_SliderLinear2D, 'Lineal 2D', 'PIVOT_BOUNDBOX'),
        )
    },
    APNODE_Image,
    APNODE_Label,
    # None,
    # {
    #     'name': 'Action Buttons',
    #     'icon': 'FILE_SCRIPT',
    #     'items': (
    #         (APNODE_ButtonScript, 'Custom Script', 'TEXT'),
    #     )
    # },
)
