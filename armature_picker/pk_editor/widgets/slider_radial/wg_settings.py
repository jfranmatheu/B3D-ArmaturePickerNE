from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_SliderRadial_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'slider_radial'

    def draw(self, layout: UILayout) -> None:
        pass
