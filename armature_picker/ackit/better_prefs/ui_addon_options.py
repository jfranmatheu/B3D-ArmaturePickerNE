from bpy.types import Event, Menu, UILayout, Context, Operator
from bpy.props import StringProperty

from .op_addon_remove import BETTERPREFS_OT_addon_remove
from .op_show_addon_folder import BETTERPREFS_OT_show_addon_folder

from bpy.app.translations import (
    pgettext_iface as iface_,
    pgettext_tip as tip_,
)


_module_name = ''


class BETTERPREFS_OT_show_addon_options(Operator):
    bl_label = "Addon Options"
    bl_idname = 'betterprefs.show_addon_options'

    module_name: StringProperty()

    def invoke(self, context: Context, event: Event):
        global _module_name
        _module_name = self.module_name
        context.window_manager.popup_menu(BETTERPREFS_MT_addon_options.draw)
        return {'INTERFACE'}


class BETTERPREFS_MT_addon_options(Menu):
    bl_label = "Addon Options"
    bl_idname = 'BETTERPREFS_MT_addon_options'

    def __init__(self) -> None:
        super().__init__()
        print("Hello Menu")

    def draw(self, context: Context):
        global _module_name
        layout: UILayout = self.layout

        layout.operator(BETTERPREFS_OT_show_addon_folder.bl_idname, text=tip_("Show in folder"), icon='FOLDER_REDIRECT').module = _module_name

        layout.separator()

        layout.operator(BETTERPREFS_OT_addon_remove.bl_idname, text="Refresh", icon='FILE_REFRESH').module = _module_name
        layout.operator(BETTERPREFS_OT_addon_remove.bl_idname, text="Update", icon='IMPORT').module = _module_name

        layout.separator()

        layout.alert = True
        layout.operator(BETTERPREFS_OT_addon_remove.bl_idname, text="Remove", icon='CANCEL').module = _module_name
