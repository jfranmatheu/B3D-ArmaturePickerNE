import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Context, Operator
from bpy.props import StringProperty, BoolProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.node_editor.nodes.image.node import APNODE_Image
from armature_picker.node_editor.nodes.bone_picker.node import APNODE_BonePicker
from armature_picker.node_editor.nodes.button_script.node import APNODE_ButtonScript
from armature_picker.utils.node_editor import get_node_editor_view_size
from armature_picker.utils.geometry import calculate_scale_to_fit_box_in_box


class AP_OT_load_image_for_active_node(Operator, ExportHelper):
    bl_idname = 'armature_picker.load_image_for_active_node'
    bl_label = 'Load Image'
    bl_description = "Load image for active node"

    filename_ext = '.png'

    filter_glob: StringProperty(
        default='*.jpg;*.jpeg;*.png',
        options={'HIDDEN'}
    )

    fit_image_to_visible_view: BoolProperty(
        name="Fit Image to View",
        default=True
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=(APNODE_Image, APNODE_BonePicker, APNODE_ButtonScript))

    def execute(self, context):
        image = bpy.data.images.load(self.filepath)
        if image is None:
            return {'CANCELLED'}
        image.name = '.' + image.name
        active_node = context.space_data.node_tree.nodes.active
        if isinstance(active_node, APNODE_Image):
            active_node.image = image
            active_node.keep_aspect_ratio = True
        elif isinstance(active_node, (APNODE_BonePicker, APNODE_ButtonScript)) and active_node.use_image:
            active_node.image = image
            active_node.keep_aspect_ratio = True
        else:
            return {'CANCELLED'}
        if self.fit_image_to_visible_view:
            wanted_dimentions, scale_to_fit = calculate_scale_to_fit_box_in_box(get_node_editor_view_size(context), active_node.rect_transform.size)
            active_node.image_scale_x = scale_to_fit * .95
        return {'FINISHED'}
