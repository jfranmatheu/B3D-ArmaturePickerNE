from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_SliderLinear_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'slider_linear'

    def draw(self, layout: UILayout) -> None:
        pass
