from bpy.types import PropertyGroup, UILayout
from bpy.props import BoolProperty
from .._base_wg_settings import SettingsBase


class PG_BonePicker_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'bone_picker'

    def draw(self, layout: UILayout) -> None:
        pass
