from .._base import AP_Node, Node
from .._transform_props import RectTransform
from .node_props import APNODE_Label_NodeProps, Label_Style

from mathutils import Vector

import bpy
from bpy.types import Context, UILayout

from ....gpu import draw
from ....utils.geometry import rotate_point


class APNODE_Label(APNODE_Label_NodeProps, AP_Node, Node):
    bl_idname = 'AP_NODE_label'
    bl_label = 'LABEL'
    bl_icon = 'FILE_FONT'
    wg_type = 'label'

    interactable = False

    draw_layer = 2


    def init(self, context):
        super().init(context)
        self.text = self.text # BUG: needs to trigger an update for dimensions...


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, rect: RectTransform, style: Label_Style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        

        padding = 4 * scale
        size = rect.size
        pos = rect.position
        padding = 4 * scale
        label_dimensions = size
        pivot = (0.5, 0.5)
        tex_pos = pos + Vector((padding, padding))

        draw.text_cached(
            self.uuid, 'LABEL', self.dirty, self.dirty_label,
            tex_pos,
            Vector(rect.origin) if rect.rotation == 0 else rotate_point(pos + Vector((padding, padding)), Vector(rect.origin), rect.rotation),
            self.text,
            self.text_size,
            label_dimensions,
            pivot=pivot if rect.rotation == 0 else (0, 0),
            angle=rect.rotation,
            color=style.text_color,
            origin=Vector(rect.origin)
        )


    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.row().prop(rect_transform, 'origin') # old location
        layout.row().prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'rotation')

        layout.prop(self, 'draw_depth')
