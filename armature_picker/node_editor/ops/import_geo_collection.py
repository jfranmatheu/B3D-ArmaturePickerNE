from bpy.types import Context, Event, Operator, Node, Collection, Scene
from bpy.props import EnumProperty, IntProperty, BoolProperty
from mathutils import Vector
import bpy

from armature_picker.node_editor.poll import poll_check
from ...utils.operator import OpsReturn, add_modal_handler
from ...utils.node_editor import get_node_editor_offset, get_node_editor_zoom
from .move_nodes import MoveNodesModal, AP_Node


collection_name: str = 'NONE'


collection_list = []
def get_collections(self, context: Context):
    collection_list.clear()
    for coll in context.scene.collection.children_recursive:
        collection_list.append((coll.name, coll.name_full, ""))
    return collection_list


class AP_OT_import_geo_collection(MoveNodesModal, Operator):
    bl_idname = 'armature_picker.import_geo_collection'
    bl_label = 'Import Geo Collection'
    bl_description = "Import all geometry from collection and turn it into a cool picker"
    bl_property = 'collection'

    collection: EnumProperty(
        name="Collection",
        items=get_collections,
        # options={'HIDDEN'}
    )

    use_object_color: BoolProperty(
        name="Use Source Object Color",
        default=False
    )

    px_per_meter: IntProperty(
        name="Scale",
        default=100,
        min=10,
        max=256,
    )

    apply_rotation: BoolProperty(
        name="Apply Rotations",
        default=False,
    )

    apply_scale: BoolProperty(
        name="Apply Scales",
        default=False,
    )

    center_origins: BoolProperty(
        name="Center Origins",
        default=False
    )


    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False)


    # def draw(self, context: Context):
    #     layout = self.layout
    #     layout.prop_search(self, 'collection', context.scene.collection, 'children')
    #     # return super().draw(context)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        # global collection_name
        # if collection_name is None:
        #     if res := context.window_manager.invoke_search_popup(self):
        #         return res
        # bpy.ops.armature_picker.import_geo_collection()
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        if self.collection == '':
            return OpsReturn.CANCEL

        collection_list: list[Collection] = context.scene.collection.children_recursive
        for coll in collection_list:
            if coll.name == self.collection:
                break

        valid_objects = []

        for ob in coll.objects:
            if ob.type != 'MESH':
                continue
            if ob.dimensions[-1] != 0:
                continue
            if len(ob.data.vertices) < 3:
                continue

            valid_objects.append(ob)

        if len(valid_objects) == 0:
            return OpsReturn.CANCEL

        from .add_node.op_add_node import new_node
        from ..nodes import APNODE_BonePickerGeo

        bones = context.active_object.data.bones
        nodes = []

        # MID-POINT for offset transform.
        mid_point = Vector((0, 0))

        # --------------------------------------
        # APPLY SCALE, ROTATION AND PIVOT TO GEOMETRY.
        if self.apply_rotation or self.apply_scale or self.center_origins:
            active_object = context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')

            for ob in context.selected_objects:
                ob.select_set(False)
            for ob in valid_objects:
                ob.select_set(True)
            context.view_layer.objects.active = valid_objects[0]

            if self.apply_rotation or self.apply_scale:
                bpy.ops.object.transform_apply(location=False, rotation=self.apply_rotation, scale=self.apply_scale)
            if self.center_origins:
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS') # 'MEDIAN

            for ob in valid_objects:
                ob.select_set(False)

            active_object.select_set(True)
            context.view_layer.objects.active = active_object
            bpy.ops.object.mode_set(mode='POSE')
        # --------------------------------------

        z_depth = []
        for ob in valid_objects:
            z_depth.append(ob.location.z)
            mid_point += Vector((ob.location.x, ob.location.y))
        mid_point /= len(valid_objects)

        min_depth = min(z_depth)
        max_depth = max(z_depth)
        depth_range = max_depth - min_depth
        if depth_range < 0.01:
            depth_mult = 1000
        elif depth_range < 0.1:
            depth_mult = 100
        elif depth_range < 2:
            depth_mult = 10
        else:
            depth_mult = 1

        # MOVE CURSOR TO THE CENTER OF THE EDITOR.
        region_mid = (int(context.area.x + context.area.width / 2), int(context.area.y + context.area.height / 2))
        context.window.cursor_warp(*region_mid)

        # GET SOME VARS TO PROJECT THE GEOMETRY IN THE PICKER VIEW2D.
        mouse_region_pos = Vector((int(context.area.width / 2), int(context.area.height / 2)))
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        troncal_node = None

        for ob in valid_objects:
            # Project coordinates.
            reg_pos = (Vector((ob.location.x * zoom, ob.location.y * zoom)) - mid_point * zoom) * self.px_per_meter
            p = (reg_pos + mouse_region_pos - offset) * inv_zoom

            # Create node and attach Object to it.
            geo_node: APNODE_BonePickerGeo = new_node(
                context, APNODE_BonePickerGeo.bl_idname, p)
            geo_node.load_shape_from_geometry(context, ob, scale=self.px_per_meter)
            geo_node.draw_depth = int(ob.location.z * depth_mult)

            # If the object name matches any bone, link it to the node.
            if bone := bones.get(ob.name):
                geo_node['_bone_name'] = bone.name
                if troncal_node is None and bone.head_local.x == 0 and bone.tail_local.x == 0:
                    troncal_node = geo_node
            geo_node.bone_loc_constraint = 'NONE'
            geo_node.bone_name = 'NONE'

            nodes.append(geo_node)

        if troncal_node is not None:
            ox = troncal_node.rect_transform.origin[0]
            for geo_node in nodes:
                geo_node['_ox_diff'] = geo_node.rect_transform.origin[0] - ox
        #     nodes.insert(0, nodes.pop(nodes.index(troncal_node)))

        for node in nodes:
            node.select = True
            node.style.use_object_color = self.use_object_color

        self.troncal_node = troncal_node
        self.modal_nodes = nodes
        self.modal__move_node__enter(context, None, mouse_region_pos)
        return add_modal_handler(context, self)

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            pass
        else:
            for geo_node in self.modal_nodes:
                if '_bone_name' in geo_node:
                    geo_node.bone_name = geo_node['_bone_name']
                    del geo_node['_bone_name']

        if self.troncal_node is not None:
            for geo_node in self.modal_nodes:
                del geo_node['_ox_diff']
            del self.troncal_node

        super().modal__move_node__exit(context, mouse_pos, cancel)

    def apply_custom_constraints(self) -> None:
        if self.troncal_node is None:
            return

        troncal_node = self.troncal_node
        ox = troncal_node.rect_transform.origin[0]
        if ox == 0:
            return
        for geo_node in self.modal_nodes:
            geo_node.rect_transform.origin[0] = geo_node['_ox_diff']
