from .bone_picker.node import AP_BonePickerNode
from .bone_picker_geo.node import APNODE_BonePickerGeo
from .image.node import APNODE_Image
from .label.node import APNODE_Label
from .sliders.linear.node import APNODE_SliderLinear
from .sliders.radial.node import APNODE_SliderRadial
from .sliders.linear_2d.node import APNODE_SliderLinear2D

NODES = (
    {
        'name': 'Picker Buttons',
        'items': (
            AP_BonePickerNode,
            APNODE_BonePickerGeo,
        )
    },
    APNODE_Image,
    APNODE_Label,
    {
        'name': 'Sliders',
        'items': (
            APNODE_SliderLinear,
            APNODE_SliderRadial,
            APNODE_SliderLinear2D,
        )
    }
)
