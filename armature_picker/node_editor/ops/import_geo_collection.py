from bpy.types import Context, Event, Operator, Node, Collection
from bpy.props import EnumProperty, IntProperty
from mathutils import Vector
import bpy

from armature_picker.node_editor.poll import poll_check
from ...utils.operator import OpsReturn
from .add_node.op import ARMATURE_PICKER_OT_add_node, get_mouse_pos, get_node_editor_offset, get_node_editor_zoom
from ...utils.node_editor import get_node_editor_view_point, get_node_editor_offset



class AP_OT_import_geo_collection(ARMATURE_PICKER_OT_add_node, Operator):
    bl_idname = 'armature_picker.import_geo_collection'
    bl_label = 'Import Geo Collection'
    bl_description = "Import all geometry from collection and turn it into a cool picker"

    collection: EnumProperty(
        name="Collection",
        items=lambda op, ctx: [(coll.name, coll.name_full, "") for coll in ctx.scene.collection.children]
    )

    px_per_meter: IntProperty(
        name="Scale",
        description="Equivalent to aprox. Pixels/Meter * 2 (when zoom-in to max).",
        default=20,
        min=10,
        max=256,
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        self.event = event
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        if self.collection == '':
            return OpsReturn.CANCEL

        coll: Collection = context.scene.collection.children.get(self.collection, None)
        if coll is None:
            return OpsReturn.CANCEL

        # from ..node_tree import AP_NodeTree
        from ..nodes import APNODE_BonePickerGeo
        # node_tree: AP_NodeTree = context.space_data.node_tree

        pose_bones = context.active_object.pose.bones
        new_node = ARMATURE_PICKER_OT_add_node.new_node

        nodes = []
        valid_objects = []

        # MID-POINT for offset transform.
        mid_point = Vector((0, 0))

        for ob in coll.objects:
            if ob.type != 'MESH':
                continue
            if ob.dimensions[-1] != 0:
                continue
            if len(ob.data.vertices) < 3:
                continue
            mid_point += Vector((ob.location.x, ob.location.y))
            valid_objects.append(ob)

        mid_point /= len(valid_objects)

        # MOVE CURSOR TO THE CENTER OF THE EDITOR.
        region_mid = (int(context.area.x + context.area.width / 2), int(context.area.y + context.area.height / 2))
        context.window.cursor_warp(*region_mid)
        
        # GET SOME VARS TO PROJECT THE GEOMETRY IN THE PICKER VIEW2D.
        mouse_region_pos = Vector((int(context.area.width / 2), int(context.area.height / 2)))
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        for ob in valid_objects:
            # Project coordinates.
            reg_pos = (Vector((ob.location.x * zoom, ob.location.y * zoom)) - mid_point) * self.px_per_meter
            p = (reg_pos + mouse_region_pos - offset) * inv_zoom

            # Create node and attach Object to it.
            geo_node: APNODE_BonePickerGeo = new_node(
                self, context, APNODE_BonePickerGeo.bl_idname, p)
            geo_node.object = ob

            # If the object name matches any bone, link it to the node.
            if bone := pose_bones.get(ob.name):
                geo_node.bone_name = bone.name

            nodes.append(geo_node)

        for node in nodes:
            node.select = True

        self.modal_nodes = nodes
        return ARMATURE_PICKER_OT_add_node.invoke(self, context, self.event)

        return OpsReturn.FINISH
