from bpy.types import Context, Event, Operator
from bpy.props import StringProperty

from armature_picker.utils.operator import OpsReturn
from armature_picker.prefs import get_prefs


class AP_OT_new_theme(Operator):
    bl_idname = 'armature_picker.new_theme'
    bl_label = 'New Theme'
    bl_description = "Create a new theme"

    name: StringProperty(name="Name", default="")

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> OpsReturn:
        new_theme = get_prefs(context).user_themes.add()
        new_theme.name = f'Theme.{len(get_prefs(context).user_themes)}' if self.name == '' else self.name
        get_prefs(context).active_theme_id = new_theme.name
        return OpsReturn.FINISH


class AP_OT_remove_theme(Operator):
    bl_idname = 'armature_picker.remove_theme'
    bl_label = 'Remove Theme'
    bl_description = "Removes active theme"

    def execute(self, context: Context) -> OpsReturn:
        prefs = get_prefs(context)
        if prefs.active_theme_id == 'DEFAULT':
            return OpsReturn.CANCEL
        prefs.user_themes.remove(prefs.active_theme_id)
        return OpsReturn.FINISH
