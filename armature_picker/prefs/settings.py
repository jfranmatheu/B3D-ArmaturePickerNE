from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import PointerProperty, StringProperty, EnumProperty

from ..utils.ui_layout import draw_section
from .wg_settings import *


class PG_ArmaturePicker_WidgetSettings(PropertyGroup):
    bone_picker: PointerProperty(type=BonePicker_Settings)
    bone_picker_geo: PointerProperty(type=BonePickerGeo_Settings)

    slider_linear: PointerProperty(type=SliderLinear_Settings)
    slider_radial: PointerProperty(type=SliderRadial_Settings)
    slider_linear_2d: PointerProperty(type=SliderLinear2D_Settings)

    image: PointerProperty(type=Image_Settings)

    label: PointerProperty(type=Label_Settings)

    wg_type: EnumProperty(
        name="Widget Type",
        items=(
            # ('label', 'Label', ""),
            # ('bone_picker', 'Bone Picker', ""),
            ('bone_picker_geo', 'Bone Picker Geo', ""),
            # ('slider_linear', 'Slider Lineal', ""),
            # ('slider_radial', 'Slider Radial', ""),
            # ('slider_linear_2d', 'Slider Lineal 2D', ""),
        )
    )

    def draw(self, layout: UILayout) -> None:
        row = layout.split(factor=.25, align=True)
        col = row.column(align=True)
        col.use_property_split = False
        col.scale_x = 1.2
        col.scale_y = 1.2
        col.prop(self, 'wg_type', text=' ', icon='NONE', expand=True)
        data = getattr(self, self.wg_type)
        name = UILayout.enum_item_name(self, 'wg_type', self.wg_type)
        data.draw(draw_section(row.column(), name, icon='NONE'))
