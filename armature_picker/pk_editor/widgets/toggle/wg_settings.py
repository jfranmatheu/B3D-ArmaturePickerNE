from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_Toggle_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'toggle'

    def draw(self, layout: UILayout) -> None:
        pass
