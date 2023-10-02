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
import tempfile


class BETTERPREFS_OT_addon_remove(Operator):
    bl_label = 'Remove Addon'
    bl_idname = 'betterpreferences.addon_remove'

    module: StringProperty()

    def execute(self, context: Context):
        path, isdir = PREFERENCES_OT_addon_remove.path_from_addon(self.module)
        if path is None:
            self.report({'WARNING'}, tip_("Add-on path %r could not be found") % path)
            return {'CANCELLED'}

        def move_file_to_temp(func, path, err):
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
                os.rename(path, os.path.join(tmpdir.name, os.path.basename(path)))
            # os.rename(path, os.path.join(bpy.utils.user_resource('SCRIPTS', path="trash"), os.path.basename(path)))

        # in case its enabled
        addon_utils.disable(self.module, default_set=True)

        import shutil
        if isdir and (not os.path.islink(path)):
            shutil.rmtree(path, onerror=move_file_to_temp)
        else:
            os.remove(path)

        addon_utils.modules_refresh()

        context.area.tag_redraw()
        return {'FINISHED'}
