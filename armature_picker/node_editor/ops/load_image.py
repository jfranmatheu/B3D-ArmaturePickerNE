import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Context, Operator
from bpy.props import StringProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.node_editor.nodes.image.node import APNODE_Image
from armature_picker.node_editor.nodes.bone_picker.node import AP_BonePickerNode


class AP_OT_load_image_for_active_node(Operator, ExportHelper):
    bl_idname = 'armature_picker.load_image_for_active_node'
    bl_label = 'Load Image'
    bl_description = "Load image for active node"
    
    filename_ext = '.png'

    filter_glob: StringProperty(
        default='*.jpg;*.jpeg;*.png',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_node=(APNODE_Image, AP_BonePickerNode))

    def execute(self, context):
        image = bpy.data.images.load(self.filepath)
        if image is None:
            return {'CANCELLED'}
        image.name = '.' + image.name
        active_node = context.space_data.node_tree.nodes.active
        if isinstance(active_node, APNODE_Image):
            active_node.image = image
        elif isinstance(active_node, AP_BonePickerNode) and active_node.use_image:
            active_node.image = image
        return {'FINISHED'}
