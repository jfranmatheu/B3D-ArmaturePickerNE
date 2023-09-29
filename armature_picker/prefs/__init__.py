from ..ackit._globals import __main_package__
from .prefs import ArmaturePickerPreferences, Context, PG_ArmaturePickerTheme, PG_ArmaturePicker_WidgetSettings


def get_prefs(context: Context) -> ArmaturePickerPreferences:
    return context.preferences.addons[__main_package__].preferences

def get_active_theme_style(context: Context) -> PG_ArmaturePickerTheme:
    return get_prefs(context).active_theme

def get_prefs_wg_settings(context: Context) -> PG_ArmaturePicker_WidgetSettings:
    return get_prefs(context).wg_settings
