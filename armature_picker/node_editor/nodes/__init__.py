from .bone_picker.node import AP_BonePickerNode
from .bone_picker_geo.node import APNODE_BonePickerGeo
from .image.node import APNODE_Image
from .label.node import APNODE_Label
from .sliders.linear.node import APNODE_SliderLinear
from .sliders.radial.node import APNODE_SliderRadial
from .sliders.linear_2d.node import APNODE_SliderLinear2D
from .button_script.node import APNODE_ButtonScript


NODES = (
    {
        'name': 'Picker Buttons',
        'items': (
            AP_BonePickerNode,
            APNODE_BonePickerGeo,
        )
    },
    APNODE_Image,
    {
        'name': 'Sliders',
        'items': (
            APNODE_SliderLinear,
            APNODE_SliderRadial,
            APNODE_SliderLinear2D,
        )
    },
    APNODE_Label,
    None,
    {
        'name': 'Action Buttons',
        'items': (
            APNODE_ButtonScript,
        )
    },
)
