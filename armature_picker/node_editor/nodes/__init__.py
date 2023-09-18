from .bone_picker.node import AP_BonePickerNode
from .bone_picker_geo.node import APNODE_BonePickerGeo
from .image.node import APNODE_Image
from .label.node import APNODE_Label
from .sliders.lineal.node import APNODE_Slider
from .sliders.radial.node import APNODE_SliderRadial
from .sliders.lineal_2d.node import APNODE_Slider2D

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
            APNODE_Slider,
            APNODE_SliderRadial,
            APNODE_Slider2D,
        )
    }
)
