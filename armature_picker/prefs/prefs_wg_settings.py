from bpy.types import PropertyGroup, UILayout
from bpy.props import PointerProperty, EnumProperty

from ..utils.ui_layout import draw_section
from armature_picker.pk_editor.widgets._base_wg_settings import SettingsBase
from armature_picker.utils.classes import get_subclasses_recursive, pack_classes_by_modules


WG_SETTING_CLASSES = pack_classes_by_modules(get_subclasses_recursive(SettingsBase, only_outermost=True), one_per_module=True)


class PG_ArmaturePicker_WidgetSettings(PropertyGroup):
    # bone_picker: PointerProperty(type=WG_SETTING_CLASSES['bone_picker'])
    bone_picker_geo: PointerProperty(type=WG_SETTING_CLASSES['bone_picker_geo'])

    # slider_linear: PointerProperty(type=WG_SETTING_CLASSES['slider_linear'])
    # slider_radial: PointerProperty(type=WG_SETTING_CLASSES['slider_radial'])
    # slider_linear_2d: PointerProperty(type=WG_SETTING_CLASSES['slider_linear_2d'])

    # image: PointerProperty(type=WG_SETTING_CLASSES['image'])

    # label: PointerProperty(type=WG_SETTING_CLASSES['label'])

    # button_script: PointerProperty(type=WG_SETTING_CLASSES['button_script'])

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
