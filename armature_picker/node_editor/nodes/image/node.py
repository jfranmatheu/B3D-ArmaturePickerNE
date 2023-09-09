from .._base import AP_Node, Node
from .node_props import APNODE_Image_NodeProps

import bpy
from bpy.types import Context, Event, UILayout

from ....gpu import draw
from ....paths import Paths



class APNODE_Image(APNODE_Image_NodeProps, AP_Node, Node):
    bl_idname = 'AP_NODE_image'
    bl_label = 'Image'
    bl_icon = 'IMAGE_DATA'

    draw_layer = 0

    def init(self, context):
        super().init(context)
        self.label = 'Image'
        
        image = bpy.data.images.get('Sav Martin es Muy Cool')
        if not image:
            image = bpy.data.images.load(str(Paths.IMAGES.joinpath('default_image.jpg')))
            image.name = 'Sav Martin es Muy Cool'
        self.image = image

    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if self.image is not None:
            draw.image(
                self.uuid, 'IMAGE', self.dirty, # CACHE.
                self.position, self.size, self.rotation, # TRANSFORM.
                self.image
            )
        else:
            draw.rectangle(
                self.uuid, 'IMAGE', self.dirty, # CACHE.
                self.position, self.size, self.rotation, # TRANSFORM.
                (1.0, 0.0, 1.0, 1.0)
            )


    def draw__edit(self, context, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            draw.box(
                self.uuid, 'IMAGE_BOX_ACTIVE', self.dirty,
                self.position, self.size, self.rotation,
                line_thickness=(3 * scale) if active else 2.5 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (.32, .64, 1.0, 1.0)
            )

    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout) -> None:
        layout.prop(self, 'origin')
        layout.prop(self, 'rotation')
        layout.prop(self, 'keep_aspect_ratio')
        # if self.keep_aspect_ratio:
        #     layout.prop(self, 'image_scale')
        # else:
        layout.prop(self, 'scale')

        _sub = layout.column()
        _sub.enabled = False
        _sub.prop(self, 'dimensions')
