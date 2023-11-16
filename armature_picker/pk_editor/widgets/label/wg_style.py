from bpy.types import UILayout

from armature_picker.ackit import ACK
from .._base_wg_style import StyleBase


@ACK.Deco.PROP_GROUP.CHILD
class PG__Label__Style(StyleBase):
    text_color: ACK.Prop.COLOR_RGBA("Text Color", (.92, .92, .92, 1.0))

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        layout.prop(self, 'text_color')
