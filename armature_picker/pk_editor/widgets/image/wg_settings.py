from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_Image_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'image'
    
    def draw(self, layout: UILayout) -> None:
        pass
