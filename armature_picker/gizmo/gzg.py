import bpy
from bpy.types import Context, GizmoGroup as GZG
from mathutils import Vector

from .gz import TheAPGZ
from .km import TheAPGZKM

from armature_picker.node_editor.poll import poll_check
from armature_picker.ackit.bcy.cy_structs import CyBlStruct
from armature_picker.utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_view_size


class TheAPGZG(GZG, TheAPGZKM):
    bl_idname: str = 'NODEEDITOR_GZG_armature_picker'
    bl_label: str = 'Armature Picker'
    bl_space_type: str = 'NODE_EDITOR'
    bl_region_type: str = 'WINDOW'
    bl_options: set[str] = {'PERSISTENT', 'SHOW_MODAL_ALL'}


    @classmethod
    def poll(cls, context: Context) -> bool:
        return poll_check(context)

    def invoke_prepare(gzg, context: Context, gz: TheAPGZ) -> None:
        # print("TheAPGZG::invoke_prepare", gz.bl_idname)
        pass

    def setup(gzg, context: Context):
        # print("TheAPGZG::setup")
        gz = gzg.gizmos.new(TheAPGZ.bl_idname)
        gz.use_event_handle_all = True
        gz.use_draw_modal = True
        gz.scale_basis = 1.0
        gzg.the_gz = gz
        gzg.reg_size = context.region.width, context.region.height

    def draw_prepare(gzg, context: Context):
        node_tree = context.space_data.node_tree
        if 'CENTER_VIEW' not in node_tree.picker_update_flags:
            return

        node_tree.picker_update_flags.remove('CENTER_VIEW')

        if len(node_tree.nodes) == 0:
            return

        zoom = get_node_editor_zoom(context)

        min_p = Vector((0, 0))
        max_p = Vector((0 ,0))

        for node in node_tree.nodes:
            # x, y = node.rect_transform.origin
            # min_p.x = min(min_p.x, x)
            # max_p.x = max(max_p.x, x)
            # min_p.y = min(min_p.y, y)
            # max_p.y = max(max_p.y, y)
            for co in node.rect_transform.coords_rotated:
                x, y = co
                min_p.x = min(min_p.x, x)
                max_p.x = max(max_p.x, x)
                min_p.y = min(min_p.y, y)
                max_p.y = max(max_p.y, y)

        '''
        # THIS NEEDS TO BE DONE IN A SECOND PASS,
        # AFTER THESE CHANGES TAKE EFFECT.
        tot_size = max_p - min_p
        view_size = get_node_editor_view_size(context)

        void_space = (view_size - tot_size) * 0.5
        min_p -= void_space
        max_p -= void_space
        '''

        pad = 5 * zoom
        pad_v = Vector((pad, pad))
        min_p -= pad_v
        max_p += pad_v

        cy_region = CyBlStruct.UI_REGION(context.region)
        # print(cy_region.v2d.cur.xmin, cy_region.v2d.cur.xmax, cy_region.v2d.cur.ymin, cy_region.v2d.cur.ymax)

        cy_region.v2d.cur.xmin = min_p.x
        cy_region.v2d.cur.xmax = max_p.x
        cy_region.v2d.cur.ymin = min_p.y
        cy_region.v2d.cur.ymax = max_p.y

        '''
        # Center View.
        mid_point = Vector((0, 0))
        for node in node_tree.nodes:
            mid_point += Vector(node.rect_transform.origin)
        mid_point /= len(node_tree.nodes)

        prev_sel = list(context.selected_nodes)
        for node in prev_sel:
            node.select = False

        any_real_node = node_tree.nodes[0]
        any_real_node.select = True
        prev_location = any_real_node.location.copy()
        any_real_node.location = mid_point

        bpy.ops.node.view_selected(False)

        any_real_node.location = prev_location
        any_real_node.select = False

        for node in prev_sel:
            node.select = True
        '''


    def refresh(gzg, context: Context):
        reg_size = context.region.width, context.region.height
        if not all([x==y for x, y in zip(reg_size, gzg.reg_size)]):
            context.region.tag_redraw()
            gzg.reg_size = reg_size
            context.space_data.node_tree.on_region_resize(context)
