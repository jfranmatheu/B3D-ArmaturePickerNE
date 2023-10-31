from .._base import AP_Node, Node, Vector
from .._transform_props import RectTransform
from .node_props import APNODE_Image_NodeProps, Image_Style

import bpy
from bpy.types import Context, Event, UILayout

from ....gpu import draw
from ....paths import Paths
from armature_picker.utils.node_editor import get_node_editor_view_size, get_armature_picker_editor
from armature_picker.utils.geometry import calculate_scale_to_fit_box_in_box


class APNODE_Image(APNODE_Image_NodeProps, AP_Node, Node):
    bl_idname = 'AP_NODE_image'
    bl_label = 'Image'
    bl_icon = 'IMAGE_DATA'
    wg_type = 'image'

    interactable: bool = False

    draw_layer = 0

    def init(self, context):
        super().init(context)
        self.label = 'Image'

        image = bpy.data.images.get('Default ArmaturePicker Image')
        if not image:
            image = bpy.data.images.load(Paths.LIB_IMAGES('default_image.png'))
            image.name = 'Default ArmaturePicker Image'
        self.image = image

        self.keep_aspect_ratio = True
        # wanted_dimentions, scale_to_fit = calculate_scale_to_fit_box_in_box(self.node_tree.view_size, image.size)
        self.image_scale_x = .25 # scale_to_fit


    # ----- DRAWING --------------------------------

    def draw_common(self, context: Context, view_loc: Vector, rect: RectTransform, style: Image_Style, wg_settings: Image_Style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        #

        if self.image is not None:
            draw.image_ui_opa(
                self, 'IMAGE',
                image=self.image,
                opa=style.opacity
            )
        else:
            draw.rectangle_ui(
                self, 'IMAGE',
                color=(1.0, 0.0, 1.0, 1.0)
            )


    # ----- UI LAYOUT DRAWING -----------------------------------------------------------

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(self, 'keep_aspect_ratio', text="Keep Image Aspect Ratio")

        layout.row().prop(rect_transform, 'origin')
        layout.row().prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'rotation')

        if self.keep_aspect_ratio:
            layout.prop(self, 'image_scale_x', text='Scale', slider=True)
        else:
            col = layout.column(align=True)
            col.prop(self, 'image_scale_x', text='Scale X', slider=True)
            col.prop(self, 'image_scale_y', text='Y', slider=True)

        _sub = layout.column()
        _sub.enabled = False
        _sub.row().prop(rect_transform, 'dimensions', text='Size')

        layout.prop(self, 'draw_depth')
