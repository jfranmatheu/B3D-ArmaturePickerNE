from bpy.types import Context, Event, Operator, Node, Collection
from bpy.props import EnumProperty
from mathutils import Vector
import bpy

from ...ops.poll import poll_node_editor
from ...utils.operator import OpsReturn



class AP_OT_import_geo_collection(Operator):
    bl_idname = 'armature_picker.import_geo_collection'
    bl_label = 'Import Geo Collection'
    bl_description = "Import all geometry from collection and turn it into a cool picker"

    collection: EnumProperty(
        name="Collection",
        items=lambda op, ctx: [(coll.name, coll.name_full, "") for coll in ctx.scene.collection.children]
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_node_editor(context)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        if self.collection == '':
            return OpsReturn.CANCEL

        coll: Collection = context.scene.collection.children.get(self.collection, None)
        if coll is None:
            return OpsReturn.CANCEL

        from ..node_tree import AP_NodeTree
        from ..nodes import APNODE_BonePickerGeo
        node_tree: AP_NodeTree = context.space_data.node_tree

        pose_bones = context.active_object.pose.bones

        for ob in coll.objects:
            if ob.type != 'MESH':
                continue
            if ob.dimensions[-1] != 0:
                continue
            if len(ob.data.vertices) < 3:
                continue

            geo_node: APNODE_BonePickerGeo = node_tree.nodes.new(APNODE_BonePickerGeo.bl_idname)
            geo_node.rect_transform.origin = Vector((ob.location.x, ob.location.y)) * geo_node.geo_scale
            geo_node.color = ob.color
            geo_node.object = ob

            if bone := pose_bones.get(ob.name):
                geo_node.bone_name = bone.name

        return OpsReturn.FINISH
