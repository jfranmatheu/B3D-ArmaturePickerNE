from .._base import AP_Node, Node
from .node_props import APNODE_Label_NodeProps
from .style_props import APNODE_Label_StyleProps

import bpy
from bpy.types import Context, UILayout

from ....gpu import draw


class APNODE_Label(APNODE_Label_NodeProps, APNODE_Label_StyleProps, AP_Node, Node):
    bl_idname = 'AP_NODE_label'
    bl_label = 'LABEL'
    bl_icon = 'FILE_FONT'

    interactable = False

    draw_layer = 2

    
    def init(self, context):
        super().init(context)
        self.text = self.text # BUG: needs to trigger an update for dimensions...


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        pos, size = self.position, self.size

        draw.text(
            # self.uuid, 'LABEL_TEXT', self.dirty, self.dirty_label,
            pos,
            self.text,
            self.text_size,
            pivot=(0, 0),
            angle=self.rotation,
            color=self.text_color
        )

    def draw__edit(self, context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            draw.box(
                self.uuid, 'LABEL_BOX_ACTIVE', self.dirty,
                self.position, self.size, self.rotation,
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)
            )
    
    
    def draw_transform(self, layout: UILayout) -> None:
        layout.prop(self, 'origin') # old location
        layout.prop(self, 'rotation')
