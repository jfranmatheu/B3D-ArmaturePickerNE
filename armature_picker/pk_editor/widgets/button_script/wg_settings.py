from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_ButtonScript_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'button_script'

    def draw(self, layout: UILayout) -> None:
        pass
