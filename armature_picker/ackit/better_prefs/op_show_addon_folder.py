import addon_utils
from bl_operators.userpref import PREFERENCES_OT_addon_remove
from bpy.app.translations import (
    pgettext_iface as iface_,
    pgettext_tip as tip_,
)
import bpy
from bpy.types import Operator, Context
from bpy.props import StringProperty

import os
from .showinfm import show_in_file_manager


class BETTERPREFS_OT_show_addon_folder(Operator):
    bl_label = 'Show Addon in Folder'
    bl_idname = 'betterpreferences.show_addon_folder'

    module: StringProperty()

    def execute(self, context: Context):
        path, isdir = PREFERENCES_OT_addon_remove.path_from_addon(self.module)
        if path is None:
            self.report({'WARNING'}, tip_("Add-on path %r could not be found") % path)
            return {'CANCELLED'}

        show_in_file_manager(os.path.dirname(path) if not isdir else path)
        return {'FINISHED'}
