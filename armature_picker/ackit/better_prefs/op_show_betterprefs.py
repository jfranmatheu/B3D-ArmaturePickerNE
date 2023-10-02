from bl_ui.space_userpref import USERPREF_PT_navigation_bar, USERPREF_HT_header
from bpy.types import Operator, Context
from bpy.props import StringProperty, BoolProperty


class BETTERPREFS_OT_toggle_betterprefs(Operator):
    bl_label = 'Toggle Addon Preferences'
    bl_idname = 'betterpreferences.stoggle_betterprefs'

    module: StringProperty()
    enable: BoolProperty()

    def execute(self, context: Context):
        addon_prefs = context.preferences.addons[self.module].preferences
        addon_prefs.show_betterprefs = self.enable

        from .ui_addon_prefs import toggle_addon_prefs
        toggle_addon_prefs(context, self.module, self.enable)

        context.area.tag_redraw()
        return {'FINISHED'}
