from bpy.types import Context, Gizmo as GZ


def get_tree(context: Context):
    return context.space_data.node_tree


class TheAPGZ(GZ):
    bl_idname: str = 'NODEEDITOR_GZ_armature_picker'

    def setup(gz): print("TheAPGZ::setup")
    def test_select(gz,c,l): return get_tree(c)._test_select(c,l)
    def invoke(gz,c,e):
        print("TheAPGZ::invoke", e.type, e.value)
        return get_tree(c)._invoke(c,e)
    def modal(gz,c,e,t):
        print("TheAPGZ::modal", e.type, e.value)
        return get_tree(c)._modal(c,e,t)
    def exit(gz,c,ca):
        print("TheAPGZ::exit", ca)
        return get_tree(c)._exit(c,ca)
    def draw(gz,c): pass # get_tree(c)._draw(c)
