from .bone_picker.node import APNODE_BonePicker
from .bone_picker_geo.node import APNODE_BonePickerGeo
from .image.node import APNODE_Image
from .label.node import APNODE_Label
from .slider_linear.node import APNODE_SliderLinear
from .slider_radial.node import APNODE_SliderRadial
from .slider_linear_2d.node import APNODE_SliderLinear2D
from .button_script.node import APNODE_ButtonScript
from .toggle.node import APNODE_Toggle


NODES = (
    (
        {
            'name': 'Bone-Picker',
            'icon': 'CONSTRAINT_BONE',
            'items': (
                (APNODE_BonePicker, 'Button', 'SEQ_SEQUENCER'),
                ((APNODE_BonePicker, 'init_preset_image'), 'Button Image', 'IMAGE_PLANE'),
                (APNODE_BonePickerGeo, 'Geometry Shape', 'MESH_MONKEY'),
            )
        },
        {
            'name': 'Action Buttons',
            'icon': 'FILE_SCRIPT',
            'items': (
                ((APNODE_ButtonScript, 'init_operator_button'), 'Operator', 'SCRIPTPLUGINS'), # 'FILE_SCRIPT'
                ((APNODE_ButtonScript, 'init_script_button'), 'Custom Script', 'TEXT'),
            )
        },
    ),
    (
        {
            'name': 'Toggle',
            'icon': 'CHECKBOX_HLT',
            'items': (
                (APNODE_Toggle, 'Radial Toggle', 'RADIOBUT_ON'),
            )
        },
        {
            'name': 'Sliders',
            'icon': 'OPTIONS',
            'items': (
                (APNODE_SliderLinear, 'Lineal', 'OPTIONS'),
                (APNODE_SliderRadial, 'Radial', 'ANTIALIASED'),
                (APNODE_SliderLinear2D, 'Lineal 2D', 'PIVOT_BOUNDBOX'),
            )
        },
    ),
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
