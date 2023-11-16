from bpy.types import UILayout, Context

from armature_picker.ackit import ACK
from .._base_wg_style import StyleBase, use_active_node


@ACK.Deco.PROP_GROUP.CHILD
class PG__Slider2D__Style(StyleBase):
    @use_active_node
    def update_handle_scale(node, _context: Context) -> None:
        node.set_state('dirty_handle_pos', True)

    color: ACK.Prop.COLOR_RGBA("Slider base color", (.18, .5, 1.0, 1.0))
    handle_color: ACK.Prop.COLOR_RGBA("Slider handle color", (.95, .9, .84, 1.0))

    handle_scale: ACK.Prop.FLOAT(
        name="Handle Scale",
        default=0.75,
        min=0.1,
        max=10,
        update=update_handle_scale
    )

    roundness: ACK.Prop.FLOAT(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=0.25,
        precision=2
    )

    outline_thickness: ACK.Prop.FLOAT(
        name="Outline Thickness",
        description="Ouline thickness of the button",
        min=0,
        max=20,
        default=0.5,
        precision=1
    )

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        col = layout.column()
        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')
        col.prop(self, 'handle_scale')

        col.separator()

        col.prop(self, 'color')
        col.prop(self, 'handle_color')
