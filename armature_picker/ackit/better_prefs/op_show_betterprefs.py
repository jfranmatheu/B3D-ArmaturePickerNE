from bl_ui.space_userpref import USERPREF_PT_navigation_bar, USERPREF_HT_header
from bpy.types import Operator, Context
from bpy.props import StringProperty, BoolProperty
import bpy


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
        
        context.space_data.show_region_header = self.enable
        for reg in context.area.regions:
            if reg.type == 'HEADER':
                do_flip = False
                if self.enable:
                    if reg.alignment == 'BOTTOM':
                        do_flip = True
                else:
                    if reg.alignment == 'TOP':
                        do_flip = True
                if do_flip:
                    with context.temp_override(window=context.window, area=context.area, region=reg):
                        bpy.ops.screen.region_flip()

        context.area.tag_redraw()
        return {'FINISHED'}
