from bpy.types import Context, Menu


class AP_MT_utils(Menu):
    bl_idname = 'AP_MT_utils'
    bl_label = "Utils"

    def draw(self, context: Context):
        layout = self.layout
        layout.operator('armature_picker.import_geo_collection')
        
        layout.separator()
        
        layout.operator('armature_picker.move_selected_to_another_layer')
