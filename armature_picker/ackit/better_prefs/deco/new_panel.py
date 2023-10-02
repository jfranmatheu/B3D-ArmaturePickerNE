from bpy.types import Panel, Context
from bl_ui.space_userpref import AddOnPanel

from ..ui_addon_prefs import get_addon_prefs, get_active_module


class BetterPrefsPanel(AddOnPanel):
    bl_label = ''
    bl_order = 0

    better_tab: str = ''
    draw_content: callable = None

    @classmethod
    def poll(cls, context: Context) -> bool:
        if get_active_module() is None:
            return False
        prefs = get_addon_prefs(context)
        return prefs is not None and prefs.show_better_preferences and hasattr(prefs, 'better_tabs') and cls.better_tab == prefs.better_tabs

    def draw(self: Panel, context: Context) -> None:
        col = self.layout.column()
        col.use_property_decorate = False
        col.use_property_split = True
        self.draw_content(col, get_addon_prefs(context))


def new_panel(tab: str, label: str, order: int, hide_header: bool = False, default_closed: bool = False):
    def wrapper(func):
        options = set()
        if hide_header:
            options.add('HIDE_HEADER')
        if default_closed:
            options.add('DEFAULT_CLOSED')
        return type(
            'BETTERPREFS_PT_' + tab.lower() + label.lower().replace(' ', '_'),
            (BetterPrefsPanel, Panel),
            {
                'bl_label': label,
                'bl_order': order,
                'bl_options': options,
                'module_name': __package__,
                'better_tab': tab,
                'draw_content': func
            }
        )

    return wrapper


def register():
    pass

def unregister():
    pass
