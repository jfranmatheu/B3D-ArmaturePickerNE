from bpy.types import Context, SpaceNodeEditor, Area
from mathutils import Vector

from armature_picker.ackit.bcy import CyBlStruct
from .geometry import Box


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

def center_node_editor_view(context: Context) -> None:
    node_tree = context.space_data.node_tree
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
    cy_region.v2d.cur.xmin = min_p.x
    cy_region.v2d.cur.xmax = max_p.x
    cy_region.v2d.cur.ymin = min_p.y
    cy_region.v2d.cur.ymax = max_p.y


def get_node_editor_visible_view_box(context: Context) -> Box:
    cy_region = CyBlStruct.UI_REGION(context.region)
    return Box(
        cy_region.v2d.cur.xmin,
        cy_region.v2d.cur.ymin,
        cy_region.v2d.cur.xmax,
        cy_region.v2d.cur.ymax)
