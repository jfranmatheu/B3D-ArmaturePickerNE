from bpy.types import PropertyGroup, UILayout

from .._base_wg_settings import SettingsBase


class PG_Label_Settings(SettingsBase, PropertyGroup):
    wg_type: str = 'label'

    def draw(self, layout: UILayout) -> None:
        pass
