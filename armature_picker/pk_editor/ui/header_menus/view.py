from bpy.types import Context, UILayout

from armature_picker.ackit import ACK
from armature_picker.ops import Ops as AP_OPS


class ViewMenu(ACK.Type.UI.MENU):
    label = "View"

    def draw_ui(self, _context: Context, layout: UILayout):
        AP_OPS.CenterView.draw_in_layout(layout)
