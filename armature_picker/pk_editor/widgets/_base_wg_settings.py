from bpy.types import UILayout, Context


class SettingsBase:
    wg_type: str

    def draw(self, layout: UILayout) -> None:
        pass
