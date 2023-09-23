from bpy.types import Context, SpaceNodeEditor, Area
from mathutils import Vector


def get_armature_picker_editor(context: Context, ret_area: bool = False) -> SpaceNodeEditor | Area:
    for area in context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            if area.spaces[0].tree_type == 'AP_NODETREE':
                return area if ret_area else area.spaces[0]
    return None


def get_node_editor_view_point(context: Context, region_point: Vector) -> Vector:
    return Vector(context.region.view2d.region_to_view(*region_point))

def get_node_editor_region_coord(context: Context, view_co: Vector) -> Vector:
    return Vector(context.region.view2d.view_to_region(*view_co, clip=False))

def get_node_editor_offset(context: Context) -> Vector:
    return Vector(context.region.view2d.view_to_region(0, 0, clip=False)) # * get_node_editor_zoom(context)

def get_node_editor_zoom(context: Context) -> float:
    region = context.region
    view2d = region.view2d
    region_height = region.height
    view_height = view2d.region_to_view(0, region_height)[1] - view2d.region_to_view(0, 0)[1]
    if view_height == 0:
        return 1
    return region_height / view_height

def get_node_editor_view_size(context: Context) -> Vector:
    region = context.region
    view2d = region.view2d
    return Vector(view2d.region_to_view(region.width, region.height)) - Vector(view2d.region_to_view(0, 0))


def deselect_all_nodes(context: Context, nullify_active: bool = True) -> None:
    if context.space_data.node_tree is not None:
        return
    for node in list(context.selected_nodes):
        node.select = False
    if nullify_active:
        context.space_data.node_tree.nodes.active = None
