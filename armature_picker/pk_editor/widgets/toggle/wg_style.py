from bpy.types import UILayout

from armature_picker.ackit import ACK
from armature_picker.pk_editor.widgets._base_wg_style import StyleBase, call_active_node_func


@ACK.Deco.PROP_GROUP.CHILD
class PG__Toggle__Style(StyleBase):
    color: ACK.Prop.COLOR_RGBA("Base color", (.21, .21, .21, 1.1))
    toggle_color: ACK.Prop.COLOR_RGBA("Toggle color", (.18, .5, 1.0, 1.1))
    roundness: ACK.Prop.FACTOR('Roundness', 1)

    def draw(self, layout: UILayout, in_prefs_space: bool = False) -> None:
        layout.prop(self, 'color')
        layout.prop(self, 'toggle_color')
