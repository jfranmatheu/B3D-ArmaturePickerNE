from bpy.types import Context, Menu


class AP_MT_view(Menu):
    bl_idname = 'AP_MT_view'
    bl_label = "View"

    def draw(self, context: Context):
        layout = self.layout
        layout.operator('armature_picker.center_view')
