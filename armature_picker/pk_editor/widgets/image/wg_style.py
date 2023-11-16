from bpy.types import UILayout

from armature_picker.ackit import ACK
from .._base_wg_style import StyleBase


@ACK.Deco.PROP_GROUP.CHILD
class PG__Image__Style(StyleBase):
    opacity: ACK.Prop.FLOAT(
        name="Opacity",
        default=1.0,
        min=0.1,
        max=1.0
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        if not in_prefs_space:
            layout.prop(self, 'opacity')
