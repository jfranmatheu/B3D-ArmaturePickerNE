from bpy.types import AddonPreferences, Context
from bpy.props import CollectionProperty, IntProperty, PointerProperty, EnumProperty

from ..ackit._globals import __main_package__
from .themes import PG_ArmaturePickerTheme


class ArmaturePickerPreferences(AddonPreferences):
    bl_idname = __main_package__
    
    def get_themes(self, context: Context) -> tuple:
        if (self.user_themes) == 0:
            return (('DEFAULT', "Default", ""),)
        else:
            return (('DEFAULT', "Default", ""), *[(th.name, th.name, '') for th in self.user_themes])

    default_theme: PointerProperty(type=PG_ArmaturePickerTheme)
    user_themes: CollectionProperty(type=PG_ArmaturePickerTheme)
    active_theme_id: EnumProperty(
        name="Active Theme",
        items=get_themes
    )
    
    @property
    def active_theme(self) -> PG_ArmaturePickerTheme:
        if self.active_theme_id == 'DEFAULT':
            return self.default_theme
        return self.user_themes[self.active_theme_id]

    def draw(self, context: Context) -> None:
        theme = self.active_theme
        theme.draw(self.layout)
