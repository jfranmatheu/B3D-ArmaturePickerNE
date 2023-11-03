import bpy
from bpy.types import NodeTree, Context, Event, Node
from mathutils import Vector

from math import cos, sin
from enum import Enum, auto
from typing import Union, List

from armature_picker.utils.cursor import Cursor, CursorIcon
from armature_picker.utils.event import Mouse, EventType, EventValue, get_mouse_pos
from ..gpu import draw
from .nodes._base import AP_Node, RectTransform
from ..utils.node_editor import get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord
from ..utils.armature import deselect_all_bones_from_active
from ..utils.geometry import angle_signed, Box, rect_overlap
from ..utils.operator import OpsReturn
from .nodes._button_common import APNODE_Button_Common
from .nodes._bone_picker_common import APNODE_BonePicker_Common
from .nodes import APNODE_Image


BonePickerNodeType = Union[AP_Node, APNODE_BonePicker_Common, APNODE_Button_Common]


class DummyPicker:
    active_node: AP_Node = None


class PickerModal(Enum):
    BOX_SELECT = auto()

    MOVE_NODE = auto()
    ROTATE_NODE = auto()
    SCALE_NODE = auto()
    RESIZE_NODE = auto()
    MOVE_NODE_CURSOR = {'update': MOVE_NODE, 'exit': MOVE_NODE}

    def __call__(self, picker: 'PickerTransformModals', context: Context, event: Event, modal_nodes: list[AP_Node] = None) -> set[str]:
        # if modal_nodes is None:
        #     from .node_tree import test_node_sel_locked
        #     modal_nodes = picker.get_selected_nodes(context, include_active=True)
        #     modal_nodes = {_node for _node in modal_nodes if test_node_sel_locked(picker, _node)}
        if modal_nodes is None:
            # MAYBE SETUP BY THE MODAL ITSELF.
            use_advanced_mouse = False
            pass
        elif isinstance(modal_nodes, AP_Node):
            use_advanced_mouse = True
        else:
            use_advanced_mouse = False
            if len(modal_nodes) == 0:
                return OpsReturn.CANCEL

        modal_id = 'modal__' + self.name.lower() + '__'
        modal_keys = {'update', 'enter', 'exit', 'draw'}
        modal_funcs = {key: None for key in modal_keys}

        if isinstance(self.value, dict):
            for modal_func_id in modal_keys:
                if other_modal_id := self.value.get(modal_func_id, None):
                    _modal_id = 'modal__' + other_modal_id.name.lower() + '__'
                    modal_funcs[modal_func_id] = getattr(picker, _modal_id + modal_func_id, None)
                else:
                    modal_funcs[modal_func_id] = getattr(picker, modal_id + modal_func_id, None)
        else:
            for modal_func_id in modal_keys:
                modal_funcs[modal_func_id] = getattr(picker, modal_id + modal_func_id, None)

        # print(modal_funcs)

        picker.set_inject_modal(
            context, event,
            modal_nodes,
            modal_callback=modal_funcs['update'],
            modal_enter_callback=modal_funcs['enter'],
            modal_exit_callback=modal_funcs['exit'],
            modal_draw_callback=modal_funcs['draw'],
            use_advanced_mouse=use_advanced_mouse
        )
        return OpsReturn.RUN


class PickerTransformModals:
    active_node: AP_Node = None
    modal_nodes: Union[List[AP_Node], List[Node]] = None
    inject_modal: callable = None
    inject_modal_exit: callable = None
    inject_modal_draw: callable = None
    inject_modal_mouse: Mouse = None

    start_modal = PickerModal


    def set_inject_modal(self,
                         context: Context,
                         event: Event,
                         modal_nodes: list[AP_Node],
                         modal_callback: callable,
                         modal_enter_callback: callable = None,
                         modal_exit_callback: callable = None,
                         modal_draw_callback: callable = None,
                         use_advanced_mouse: bool = False) -> None:

        if isinstance(modal_nodes, AP_Node):
            self.active_node = modal_nodes
            self.modal_nodes = [modal_nodes]
        else:
            self.modal_nodes = modal_nodes

        if self.modal_nodes is not None:
            self.modal__preprocess_mirror_bone_pickers(context, event)

        if use_advanced_mouse: # or self.active_node is not None:
            self.inject_modal_mouse = Mouse.init(event, context, local_space__rect=self.active_node.rect_transform if self.active_node is not None else None)
            def _modal_update_wrapper(context: Context, event: Event, mouse_pos: Vector):
                self.inject_modal_mouse.update(event, context, local_space__rect=self.active_node.rect_transform if self.active_node is not None else None)
                return modal_callback(context, event, self.inject_modal_mouse)
            self.inject_modal = _modal_update_wrapper
        else:
            self.inject_modal = modal_callback
        self.inject_modal_exit = modal_exit_callback
        self.inject_modal_draw = modal_draw_callback
        if modal_enter_callback is not None:
            modal_enter_callback(context, event, self.mouse_pos)


    def modal__preprocess_mirror_bone_pickers(self, context: Context, event: Event):
        # ----------------------------------------------------------------
        # Process bone picker nodes with mirror node. (L/R) support.
        view_pos = get_node_editor_view_point(context, get_mouse_pos(event))
        preferred_side: str = 'LEFT' if view_pos.x < 0 else 'RIGHT'
        to_remove_nodes = set()
        self.mirror_nodes: dict[BonePickerNodeType, BonePickerNodeType] = {}
        for node in self.modal_nodes:
            if not isinstance(node, APNODE_BonePicker_Common):
                continue
            if node in to_remove_nodes:
                continue
            if node.bone_loc_constraint not in {'LEFT', 'RIGHT'}:
                continue

            # Get mirror node and determine if current node is in the preferred side or not.
            keep_curr_node = preferred_side == node.bone_loc_constraint
            mirror_node = node.get_mirror_node()
            if mirror_node is None:
                continue

            mirror_node.select = True

            # Exclude mirror node (or current node, depending on the prefered side)
            # to avoid moving both L/R nodes at the same time (CAOS!)
            if mirror_node in self.modal_nodes:
                if keep_curr_node:
                    self.mirror_nodes[node] = mirror_node
                    to_remove_nodes.add(mirror_node)
                else:
                    self.mirror_nodes[mirror_node] = node
                    to_remove_nodes.add(node)
            else:
                self.mirror_nodes[node] = mirror_node

        # Safely remove nodes from the non-prefered side of the picker
        # when we detect that both L and R nodes are selected for this modal.
        if len(to_remove_nodes) != 0:
            for to_remove_node in to_remove_nodes:
                self.modal_nodes.remove(to_remove_node)

    # ----------------------------------------------------------------

    # INVOKE: Move nodes by increments in the given direction.
    # ----------------------------------------------------------------

    def move_node_increment(self, context: Context, nodes: list[AP_Node], direction: Vector) -> None:
        move_dir = direction * 10 * context.preferences.system.ui_scale
        for node in nodes:

            rect: RectTransform = node.rect_transform
            pos = Vector(rect.origin) + move_dir

            # Apply Mirror Constraints to BonePicker Widgets.
            if isinstance(node, APNODE_BonePicker_Common):
                if node.bone_loc_constraint == 'CENTER':
                    pos.x = 0 # Lock to Y axis at X=0.
                elif node.bone_loc_constraint == 'LEFT':
                    dim_right_to_origin = rect.dimensions[0] * (1 - rect.pivot[0])
                    right = pos.x + dim_right_to_origin
                    if right > 0:
                        pos.x = - dim_right_to_origin
                elif node.bone_loc_constraint == 'RIGHT':
                    dim_left_to_origin = rect.dimensions[0] * rect.pivot[0]
                    left = pos.x - dim_left_to_origin
                    if left < 0:
                        pos.x = dim_left_to_origin

                origin = tuple(int(v) for v in pos)
                rect.origin = origin

                if mirror_node := node.get_mirror_node():
                    mirror_node.rect_transform.origin = (-origin[0], origin[1])

            else:
                rect.origin = tuple(int(v) for v in pos)

        context.region.tag_redraw()


    # MODAL: Move Selected Nodes.
    # ----------------------------------------------------------------

    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_location = [tuple(node.rect_transform.origin) for node in self.modal_nodes]
        node_region_location = [get_node_editor_region_coord(context, node.rect_transform.origin) for node in self.modal_nodes]
        self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in node_region_location]

        self.modal_move_axis = {'X', 'Y'}

        Cursor.set_icon(context, CursorIcon.HAND)

    def modal__move_node_cursor__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)
        mouse_offset = (mouse_pos - offset) * inv_zoom

        # Calculate the center of the selected nodes.
        center = Vector((0, 0))
        for node in self.modal_nodes:
            center += Vector(node.rect_transform.origin)
        center /= len(self.modal_nodes)

        for node in self.modal_nodes:
            node.rect_transform.move_to(mouse_offset + (Vector(node.rect_transform.origin) - center))

        self.modal__move_node__enter(context, event, mouse_pos)

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        if event.type == 'X' and event.value == 'RELEASE':
            if 'Y' in self.modal_move_axis:
                self.modal_move_axis.remove('Y')
                self.modal_move_axis.add('X')
            else:
                self.modal_move_axis.add('Y')
        elif event.type == 'Y' and event.value == 'RELEASE':
            if 'X' in self.modal_move_axis:
                self.modal_move_axis.remove('X')
                self.modal_move_axis.add('Y')
            else:
                self.modal_move_axis.add('X')

        def move_node(_node: Node, _prev_node_origin: Vector, _node_loc_offset: Vector):
            if _node.locked:
                return

            rect: RectTransform = _node.rect_transform
            pos = (mouse_pos - offset + _node_loc_offset) * inv_zoom

            # Apply Axis and Mirror Constraints to BonePicker Widgets.
            if isinstance(_node, APNODE_BonePicker_Common):
                if _node.bone_loc_constraint == 'CENTER':
                    pos.x = 0 # Lock to Y axis at X=0.
                elif _node.bone_loc_constraint == 'LEFT':
                    dim_right_to_origin = rect.dimensions[0] * (1 - rect.pivot[0])
                    right = pos.x + dim_right_to_origin
                    if right > 0:
                        pos.x = - dim_right_to_origin
                elif _node.bone_loc_constraint == 'RIGHT':
                    dim_left_to_origin = rect.dimensions[0] * rect.pivot[0]
                    left = pos.x - dim_left_to_origin
                    if left < 0:
                        pos.x = dim_left_to_origin

                # Move mirror node accordingly if existing.
                if _mirror_node := self.mirror_nodes.get(_node, None):
                    _mirror_node.rect_transform.move_to((-pos.x, pos.y))

            if len(self.modal_move_axis) in {0, 2}:
                pass
            elif 'X' in self.modal_move_axis:
                pos.y = _prev_node_origin[1]
            elif 'Y' in self.modal_move_axis:
                pos.x = _prev_node_origin[0]

            # MOVE!
            rect.move_to(pos)

        {move_node(node, prev_loc, node_loc_offset) for (node, prev_loc, node_loc_offset) in zip(self.modal_nodes, self.prev_node_location, self.node_location_offset)}
        return 1

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.rect_transform.move_to(prev_node_loc)
                # MIRROR -----
                if isinstance(node, APNODE_BonePicker_Common):
                    if mirror_node := self.mirror_nodes.get(node, None):
                        mirror_node.rect_transform.move_to((-prev_node_loc[0], prev_node_loc[1]))

            del self.prev_node_location
            del self.node_location_offset

        del self.modal_move_axis

        Cursor.set_icon(context, CursorIcon.DEFAULT)


    # MODAL: Rotate Selected Nodes.
    # ----------------------------------------------------------------

    def modal__rotate_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_rotation = [node.rect_transform.rotation for node in self.modal_nodes]
        # self.start_mouse_pos = mouse_pos
        orig = Vector((0, 0))
        for node in self.modal_nodes:
            orig += Vector(node.rect_transform.origin)
        orig /= len(self.modal_nodes)
        self.modal_rotation_origin_view = orig
        orig = get_node_editor_region_coord(context, orig)
        self.modal_rotation_origin_region = orig
        self.modal_rotation_start_vec = (orig - mouse_pos)#.normalized()

    def modal__rotate_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1

        curr_rotation_vec = (self.modal_rotation_origin_region - mouse_pos)#.normalized()
        angle_offset = angle_signed(self.modal_rotation_start_vec, curr_rotation_vec)

        def rotate_node(_node: Node, _rot: float):
            if _node.locked:
                return

            # Apply Axis and Mirror Constraints to BonePicker Widgets.
            if isinstance(_node, APNODE_BonePicker_Common):
                # Rotate mirror node accordingly if existing.
                if _mirror_node := self.mirror_nodes.get(_node, None):
                    _mirror_node.rect_transform.rotation = -_rot

            _node.rect_transform.rotation = _rot

        {rotate_node(node, orig_rot + angle_offset) for (node, orig_rot) in zip(self.modal_nodes, self.prev_node_rotation)}
        return 1

    def modal__rotate_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_rot) in zip(self.modal_nodes, self.prev_node_rotation):
                node.rect_transform.rotation = prev_node_rot
                # MIRROR -----
                if isinstance(node, APNODE_BonePicker_Common):
                    if mirror_node := self.mirror_nodes.get(node, None):
                        mirror_node.rect_transform.rotation = -prev_node_rot

        del self.prev_node_rotation
        del self.modal_rotation_origin_region
        del self.modal_rotation_origin_view
        del self.modal_rotation_start_vec


    def modal__rotate_node__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if not in_view2d or not in_edit:
            return
        draw.text(self.modal_rotation_origin_view.copy(), 'o', 12, (0.5, 0.5), color=(1, 0, 0, 1))
        return
        print(self.modal_rotation_origin_region)
        draw.just_a_point(
            self.modal_rotation_origin_region,
            5 * ui_scale,
            color=(1, 0, 0, 1.0)
        )

    # MODAL: SCALE Selected Nodes.
    # ----------------------------------------------------------------

    def modal__scale_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        for node in self.modal_nodes:
            if isinstance(node, APNODE_Button_Common) and node.fit_to_text:
                node.fit_to_text = False

        self.prev_node_dimensions = [tuple(node.rect_transform.dimensions) for node in self.modal_nodes]
        self.modal_scale_axis = {'X', 'Y'}

        orig = Vector((0, 0))
        for node in self.modal_nodes:
            orig += Vector(node.rect_transform.origin)
        orig /= len(self.modal_nodes)
        self.modal_scale_origin_view = orig
        orig = get_node_editor_region_coord(context, orig)
        self.modal_scale_origin_region = orig
        self.modal_scale_start_dist = (mouse_pos - orig).length

        Cursor.set_icon(context, CursorIcon.SCROLL_XY)

    def modal__scale_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1

        if event.type == 'X' and event.value == 'RELEASE':
            if 'Y' in self.modal_scale_axis:
                self.modal_scale_axis.remove('Y')
                self.modal_scale_axis.add('X')
            else:
                self.modal_scale_axis.add('Y')
        elif event.type == 'Y' and event.value == 'RELEASE':
            if 'X' in self.modal_scale_axis:
                self.modal_scale_axis.remove('X')
                self.modal_scale_axis.add('Y')
            else:
                self.modal_scale_axis.add('X')

        scale_curr_dist = (mouse_pos - self.modal_scale_origin_region).length

        view_zoom = 1 / get_node_editor_zoom(context)
        mvec_dist = (scale_curr_dist - self.modal_scale_start_dist) * view_zoom
        mvoff = Vector((mvec_dist, mvec_dist))

        def scale_node(_node: AP_Node, _dim: tuple[int, int]):
            if _node.locked:
                return
            rect: RectTransform = _node.rect_transform
            dimensions = Vector(_dim) + mvoff

            # Special case for buttons with image.
            if ((isinstance(_node, APNODE_Button_Common) and _node.use_image) or isinstance(_node, APNODE_Image)) and\
                _node.image is not None and _node.keep_aspect_ratio:
                # dim.x -> scale_xsss
                # new_dim.x -> new_scale_x ?
                new_scale_x = _node.image_scale_x * dimensions[0] / _dim[0]
                _node.image_scale_x = new_scale_x

                if isinstance(_node, APNODE_BonePicker_Common):
                    # Scale mirror node image accordingly if existing.
                    if _mirror_node := self.mirror_nodes.get(_node, None):
                        # It must respect the same conditions...
                        if _mirror_node.use_image and _mirror_node.image is not None and _mirror_node.keep_aspect_ratio:
                            _mirror_node.rect_transform.dimensions = dimensions
            else:
                # Common-case.
                if len(self.modal_scale_axis) in {0, 2}:
                    pass
                elif 'X' in self.modal_scale_axis:
                    dimensions.y = _dim[1]
                elif 'Y' in self.modal_scale_axis:
                    dimensions.x = _dim[0]

                dimensions = tuple(int(v) for v in dimensions)
                rect.dimensions = dimensions

                if isinstance(_node, APNODE_BonePicker_Common):
                    # Scale mirror node accordingly if existing.
                    if _mirror_node := self.mirror_nodes.get(_node, None):
                        _mirror_node.rect_transform.dimensions = dimensions


        {scale_node(node, orig_dim) for (node, orig_dim) in zip(self.modal_nodes, self.prev_node_dimensions)}
        return 1

    def modal__scale_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_dim) in zip(self.modal_nodes, self.prev_node_dimensions):
                node.rect_transform.dimensions = prev_node_dim
                # MIRROR -----
                if isinstance(node, APNODE_BonePicker_Common):
                    if mirror_node := self.mirror_nodes.get(node, None):
                        mirror_node.rect_transform.dimensions = prev_node_dim

        del self.prev_node_dimensions
        del self.modal_scale_origin_view
        del self.modal_scale_origin_region
        del self.modal_scale_axis

        Cursor.set_icon(context, CursorIcon.DEFAULT)

    def modal__scale_node__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if in_view2d:
            pass

        else:
            draw.just_a_line(
                self.modal_scale_origin_region,
                self.mouse_pos,
                2 * ui_scale,
                (.9, .9, .9, .7)
            )
            draw.just_a_point(
                self.modal_scale_origin_region,
                4 * ui_scale,
                (0, 0, 0, 1)
            )
            draw.just_a_point(
                self.modal_scale_origin_region,
                3 * ui_scale,
                (1, 1, 1, 1)
            )


    # MODAL: Resize Selected Nodes.
    # ----------------------------------------------------------------

    def modal__resize_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        node = self.active_node
        rect: RectTransform = node.rect_transform
        node.in_modal = True

        self.prev_node_coords = list(rect.coords)
        self.node_border_id: str =node.get_state('HOVERED_BORDER', 'NONE')
        self.node_reg_loc = get_node_editor_region_coord(context, rect.origin)
        self.node_reg_loc_offset = self.node_reg_loc - mouse_pos

        self.node_bbox = Box(rect.x_min, rect.y_min, rect.x_max, rect.y_max)

        if self.node_border_id == 'LEFT':
            self.rect_border_attr = 'x_min'
            self.node_start_min = rect.x_min
        elif self.node_border_id == 'BOTTOM':
            self.rect_border_attr = 'y_min'
            self.node_start_min = rect.y_min
        elif self.node_border_id == 'RIGHT':
            self.rect_border_attr = 'x_max'
            self.node_start_min = rect.x_max
        elif self.node_border_id == 'TOP':
            self.rect_border_attr = 'y_max'
            self.node_start_min = rect.y_max

        if isinstance(node, APNODE_Button_Common) and node.fit_to_text:
            node.fit_to_text = False

        if ((node.wg_type in {'bone_picker', 'button_script'} and node.use_image) or node.wg_type == 'image') and node.image is not None:
            self.use_keep_image_aspect_ratio = node.keep_aspect_ratio
        else:
            self.use_keep_image_aspect_ratio = False

        # ----------------------------------------------------------------
        # MIRROR NODE!
        if isinstance(node, APNODE_BonePicker_Common):
            self.mirror_node = self.mirror_nodes.get(node, None)
            if self.mirror_node is not None:
                if self.mirror_node.fit_to_text:
                    self.mirror_node.fit_to_text = False
                self.prev_mirror_node_coords = list(self.mirror_node.rect_transform.coords)
        else:
            self.mirror_node = None
        # ----------------------------------------------------------------

        Cursor.set_icon(context, CursorIcon.DOT)


    def modal__resize_node__update(self, context: Context, event: Event, mouse: Mouse) -> int:
        if self.active_node is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1

        if event.type not in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            return 1

        border_id = self.node_border_id
        is_hor_border = border_id in {'LEFT', 'RIGHT'}
        is_vert_border = border_id in {'BOTTOM', 'TOP'}
        is_max_border = border_id in {'RIGHT', 'TOP'}
        is_min_border = border_id in {'LEFT', 'BOTTOM'}

        if is_hor_border and mouse.local_dir.x == 0:
            return 1
        if is_vert_border and mouse.local_dir.y == 0:
            return 1

        node = self.active_node
        rect: RectTransform = node.rect_transform

        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        # offset = get_node_editor_offset(context)

        # OLD METHOD
        # BUG ISSUE: looks like local_rect_space Mouse type stuff is wiggling around when modifying the minimum values (x_min, y_min).
        # It works for maximum values (x_max, y_max) tho.

        # print("local_current_prev ->", mouse.local_prev.x, "->", mouse.local_current.x)
        # print("local_delta_int.x ->", mouse.local_delta_int.x)
        # print("local_offset.x ->", mouse.local_offset.x)

        prev_dim = Vector(rect.dimensions)

        if self.use_keep_image_aspect_ratio:
            prev_origin = tuple(rect.origin)

        # ----------------------------------------------------------------

        if is_hor_border:
            if is_min_border:
                # X-MIN.
                value = get_node_editor_view_point(context, mouse.current).x ## rect.x_min + mouse.local_delta_int.x * inv_zoom ## self.node_start_min + mouse.local_offset.x * inv_zoom
            elif is_max_border:
                # X-MAX.
                if rect.rotation == 0:
                    value = get_node_editor_view_point(context, mouse.current).x
                else:
                    value = rect.x_max + mouse.local_delta_int.x * inv_zoom

        elif is_vert_border:
            if is_min_border:
                # Y-MIN.
                value = get_node_editor_view_point(context, mouse.current).y ## rect.y_min + mouse.local_delta_int.y * inv_zoom ## self.node_start_min + mouse.local_offset.y * inv_zoom
            elif is_max_border:
                # Y-MAX.
                if rect.rotation == 0:
                    value = get_node_editor_view_point(context, mouse.current).y
                else:
                    value = rect.y_max + mouse.local_delta_int.y * inv_zoom

        # ----------------------------------------------------------------
        # Apply Mirror Constraints to BonePicker Widgets.
        if isinstance(node, APNODE_BonePicker_Common):
            # Get the border_id that should be resized in the mirror node.
            if is_hor_border:
                if is_min_border:
                    mirror_border_attr = 'x_max'
                else:
                    mirror_border_attr = 'x_min'
                mirror_value = -value
            else:
                mirror_border_attr = self.rect_border_attr
                mirror_value = value

            # Pass to prevent overlapping in L/R mirror nodes.
            # And to maintain a consistent width for CENTER bone picker widgets.
            if is_hor_border:
                if node.bone_loc_constraint == 'CENTER':
                    setattr(node.rect_transform, mirror_border_attr, mirror_value)
                elif node.bone_loc_constraint == 'LEFT' and is_max_border:
                    if value > 0:
                        value = 0
                        mirror_value = 0
                elif node.bone_loc_constraint == 'RIGHT' and is_min_border:
                    if value < 0:
                        value = 0
                        mirror_value = 0

            # Move mirror node accordingly if existing.
            if self.mirror_node is not None:
                mirror_prev_origin = tuple(rect.origin)
                setattr(self.mirror_node.rect_transform, mirror_border_attr, mirror_value)
        # ----------------------------------------------------------------

        # Apply border displacement to node!
        setattr(node.rect_transform, self.rect_border_attr, value)


        # rect.update_from_coords(context)
        if hasattr(node, 'apply_transform_dimensions_constraints'):
            new_dim = Vector(rect.dimensions)
            if prev_dim != new_dim:
                if constrained_dimensions := node.apply_transform_dimensions_constraints(prev_dim, new_dim):
                    rect.dimensions = constrained_dimensions

        if self.use_keep_image_aspect_ratio:
            rect.origin = prev_origin
            if self.mirror_node is not None:
                self.mirror_node.rect_transform.origin = mirror_prev_origin

        node.update_graphics(context)
        if self.mirror_node is not None:
            self.mirror_node.update_graphics(context)
        return 1

    def modal__resize_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        node = self.active_node
        rect: RectTransform = node.rect_transform

        if cancel:
            rect.coords = self.prev_node_coords
            rect.update_from_coords(context)

            # ----------------------------------------------------------------
            # MIRROR CANCEL.
            if self.mirror_node is not None:
                mirror_rect: RectTransform = self.mirror_node.rect_transform
                mirror_rect.coords = self.prev_mirror_node_coords
                mirror_rect.update_from_coords(context)
            # ----------------------------------------------------------------

        elif rect.rotation != 0 or not rect.can_update_origin_on_redimension:
            v_dir_angle = (Vector(rect.coords_rotated[2]) - Vector(rect.coords_rotated[1])).normalized()

            width, height = rect.dimensions

            origin_in_local = Vector((
                rect.pivot[0] * (width - 2),
                rect.pivot[1] * (height - 1)
            ))
            rotation_angle = rect.rotation
            rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
            rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

            adjusted_origin = (
                int(rect.coords_rotated[1][0] + rotated_offset_x - v_dir_angle.x * .25),
                int(rect.coords_rotated[1][1] + rotated_offset_y - v_dir_angle.y * .25)
            )
            rect.origin = adjusted_origin

            # ----------------------------------------------------------------
            # MIRROR ADJUSTMENT.
            if self.mirror_node is not None:
                self.mirror_node.rect_transform.origin = (-adjusted_origin[0], adjusted_origin[1])
            # ----------------------------------------------------------------

        if self.mirror_node is not None:
            del self.prev_mirror_node_coords
            self.mirror_node = None

        if hasattr(self, 'node_start_min'):
            del self.rect_border_attr
            del self.node_start_min
        del self.node_border_id
        del self.prev_node_coords
        del self.node_reg_loc
        del self.node_reg_loc_offset
        del self.node_bbox
        del self.use_keep_image_aspect_ratio

        self.active_node.in_modal = False
        self.active_node = None

        Cursor.set_icon(context, CursorIcon.DEFAULT)


    # ----------------------------------------------------------------

    def modal__box_select__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.box = Box(mouse_pos.x, mouse_pos.y, mouse_pos.x, mouse_pos.y)
        self.box_origin = mouse_pos.copy()
        in_edit = self.picker_mode == 'EDIT'
        self.append_selection = event.shift
        self.modal_nodes = self.widgets_from_active_layer if in_edit else [node for node in self.widgets_from_active_layer if node.wg_type.startswith('bone_picker')]
        if in_edit:
            self.prev_sel_nodes = self.get_selected_nodes(context, include_active=True)
        else:
            self.prev_sel_nodes = {_node for _node in self.modal_nodes if _node.test_bone_selected(context)}

        if self.append_selection:
            if in_edit:
                pass
            else:
                bpy.ops.node.select_all(False, action='DESELECT')
                for prev_sel_node in self.prev_sel_nodes:
                    prev_sel_node.select = True
        else:
            bpy.ops.node.select_all(False, action='DESELECT')
            if not in_edit:
                deselect_all_bones_from_active(context)

        Cursor.set_icon(context, CursorIcon.CROSS)

    def modal__box_select__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return -1

        if event.type not in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            return 1

        ori_x, ori_y = self.box_origin
        curr_x, curr_y = mouse_pos

        if curr_x > ori_x:
            self.box.x_max = curr_x
        elif curr_x < ori_x:
            self.box.x_max = ori_x
            self.box.x_min = curr_x

        if curr_y > ori_y:
            self.box.y_max = curr_y
        elif curr_y < ori_y:
            self.box.y_max = ori_y
            self.box.y_min = curr_y

        proj_box = Box(*(get_node_editor_view_point(context, self.box.min)),
                       *(get_node_editor_view_point(context, self.box.max)))

        for node in self.modal_nodes:
            rect = node.rect_transform
            if rect_overlap(proj_box, rect):
                node.select = True
            elif node.select:
                if self.append_selection and node in self.prev_sel_nodes:
                    continue
                node.select = False

        context.region.tag_redraw()
        return 1

    def modal__box_select__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        in_pose = self.picker_mode == 'POSE'

        if cancel:
            deselect_all_bones_from_active(context)
            for sel_node in self.prev_sel_nodes:
                sel_node.select = True

        else:
            sel_nodes = [node for node in self.modal_nodes if node.select]
            if len(sel_nodes) != 0:
                self.nodes.active = sel_nodes.pop()
                if in_pose:
                    self.nodes.active.select_bone(context, deselect_all=True, make_active=True)
                    for node in sel_nodes:
                        node.select_bone(context, deselect_all=False, make_active=False)
                    for sel_node in self.prev_sel_nodes:
                        sel_node.select_bone(context, deselect_all=False, make_active=False)

                del sel_nodes

        Cursor.set_icon(context, CursorIcon.DEFAULT)

        del self.append_selection
        del self.box
        del self.box_origin
        del self.prev_sel_nodes


    def modal__box_select__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if in_view2d:
            if in_edit:
                return

            for node in self.modal_nodes:
                if node.select:
                    if hasattr(node, 'use_image'):
                        node.draw_sel_cage((.3, .7, 1.0, .92), cage_thickness=2.5, force_draw=True)
                    else:
                        node.draw_sel_cage((.3, .7, 1.0, .92), cage_thickness=2.5)

        else:
            draw.box(
                self.get_graphic_user('MODAL_BOX_SELECT'), 'BOX_SELECT',
                self.box.pos, self.box.size,
                padding=0,
                line_thickness=2.0,
                color=(1, 1, 1, .92)
            )
