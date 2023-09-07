from bpy.types import Context, GizmoGroup as GZG

from .gz import TheAPGZ
from .km import TheAPGZKM


class TheAPGZG(GZG, TheAPGZKM):
    bl_idname: str = 'NODEEDITOR_GZG_armature_picker'
    bl_label: str = 'Armature Picker'
    bl_space_type: str = 'NODE_EDITOR'
    bl_region_type: str = 'WINDOW'
    bl_options: set[str] = {'PERSISTENT', 'SHOW_MODAL_ALL'}


    @classmethod
    def poll(cls, context: Context) -> bool:
        return context.space_data.node_tree is not None and context.space_data.tree_type == 'AP_NODETREE' and context.mode in {'POSE', 'EDIT_ARMATURE'}

    def invoke_prepare(gzg, context: Context, gz: TheAPGZ) -> None:
        print("TheAPGZG::invoke_prepare", gz.bl_idname)

    def setup(gzg, context: Context):
        print("TheAPGZG::setup")
        gz = gzg.gizmos.new(TheAPGZ.bl_idname)
        gz.use_event_handle_all = True
        gz.use_draw_modal = True
        gz.scale_basis = 1.0
        gzg.the_gz = gz

    def draw_prepare(gzg, context: Context):
        pass

    def refresh(gzg, context: Context):
        pass
