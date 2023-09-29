from bpy.types import UILayout, Context


class SettingsBase:
    def draw(self, layout: UILayout) -> None:
        pass
