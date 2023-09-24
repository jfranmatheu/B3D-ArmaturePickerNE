import bpy
from bpy.types import Context, GizmoGroup as GZG
from mathutils import Vector

from .gz import TheAPGZ
from .km import TheAPGZKM

from armature_picker.node_editor.poll import poll_check
from armature_picker.ackit.bcy.cy_structs import CyBlStruct
from armature_picker.utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_view_size, center_node_editor_view


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
        center_node_editor_view(context)


    def refresh(gzg, context: Context):
        reg_size = context.region.width, context.region.height
        if not all([x==y for x, y in zip(reg_size, gzg.reg_size)]):
            context.region.tag_redraw()
            gzg.reg_size = reg_size
            context.space_data.node_tree.on_region_resize(context)
