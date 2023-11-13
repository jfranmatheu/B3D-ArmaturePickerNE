from bpy.types import PropertyGroup, UILayout
from bpy.props import BoolProperty

from .._base_wg_settings import SettingsBase


class PG_BonePickerGeo_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'bone_picker_geo'

    display_on_hover_only: BoolProperty(name="Show only on hover", description="(While in POSE mode) Display this element only when hovering over it", default=False)

    def draw(self, layout: UILayout) -> None:
        layout.prop(self, 'display_on_hover_only')
