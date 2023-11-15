import bpy
from bpy.types import Context
from bpy.props import BoolProperty

from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_check
from armature_picker.pk_editor.widgets.image.node import APNODE_Image
from armature_picker.pk_editor.widgets._button_common import APNODE_Button_Common
from armature_picker.utils.node_editor import get_node_editor_view_size
from armature_picker.utils.geometry import calculate_scale_to_fit_box_in_box


@ACK.Deco.OPS.IMPORT('PNG', 'JPG', 'JPEG')
class LoadImageForActiveNode(ACK.Type.OPS.ACTION):
    label = 'Load Image'
    tooltip = "Load image for active node"

    fit_image_to_visible_view: BoolProperty(
        name="Fit Image to View",
        default=True
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=(APNODE_Image, APNODE_Button_Common))

    def action(self, context: Context) -> None:
        image = bpy.data.images.load(self.filepath)
        if image is None:
            return self.error('Image not found!')
        image.name = '.' + image.name
        active_node = context.space_data.node_tree.nodes.active
        if isinstance(active_node, APNODE_Image):
            active_node.image = image
            active_node.keep_aspect_ratio = True
        elif isinstance(active_node, APNODE_Button_Common) and active_node.use_image:
            active_node.image = image
            active_node.keep_aspect_ratio = True
        if self.fit_image_to_visible_view:
            wanted_dimentions, scale_to_fit = calculate_scale_to_fit_box_in_box(get_node_editor_view_size(context), active_node.rect_transform.size)
            active_node.image_scale_x = scale_to_fit * .95
