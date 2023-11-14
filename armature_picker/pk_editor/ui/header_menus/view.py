from bpy.types import Context, Menu

from armature_picker.ops import Ops as AP_OPS


class AP_MT_view(Menu):
    bl_idname = 'AP_MT_view'
    bl_label = "View"

    def draw(self, context: Context):
        AP_OPS.CenterView.draw_in_layout(self.layout)
