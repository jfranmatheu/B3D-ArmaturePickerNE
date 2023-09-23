from .._base import AP_Node, Node
from .._transform_props import RectTransform
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

    def draw_common(self, context: Context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        draw.text(
            # self.uuid, 'LABEL_TEXT', self.dirty, self.dirty_label,
            rect.position,
            self.text,
            self.text_size,
            pivot=(0, 0),
            angle=rect.rotation,
            color=self.text_color
        )


    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.row().prop(rect_transform, 'origin') # old location
        layout.row().prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'rotation')

        layout.prop(self, 'draw_depth')
