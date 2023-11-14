from bpy.types import Context, UILayout

from armature_picker.ackit import ACK


class UtilsMenu(ACK.Type.UI.MENU):
    label = "Utils"

    def draw_ui(self, _context: Context, layout: UILayout):
        layout.operator('armature_picker.import_selected_bones')
        layout.operator('armature_picker.import_geo_collection')

        layout.separator()

        layout.operator('armature_picker.move_selected_to_another_layer')
