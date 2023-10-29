from bpy.types import Context, UILayout, PropertyGroup, Node, NodeTree
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, IntVectorProperty, EnumProperty, PointerProperty
from mathutils import Vector

from math import pi, cos, sin

from ...utils.geometry import rotate_point, point_inside_rect
from ...utils.node_editor import get_node_editor_region_coord, get_node_editor_zoom


class CM_BlockUpdates:
    def __init__(self, rect: 'RectTransform') -> None:
        self.rect = rect

    def __enter__(self) -> 'RectTransform':
        self.rect.block_updates = True
        return self.rect

    def __exit__(self, exc_type, exc_value, trace) -> None:
        self.rect.block_updates = False
        self.rect = None


class RectTransform(PropertyGroup):
    @property
    def node_tree(self) -> NodeTree:
        return self.id_data

    @property
    def node(self) -> Node:
        return self.node_tree.nodes.get(self.node_idname, None)

    node_idname: StringProperty(name="Node Name")

    # ----- Updates --------------------------------

    def update_dimensions(self, context: Context) -> None:
        if node := self.node:
            if hasattr(node, 'update_dimensions'):
                node.update_dimensions(context)


    def update(self, context: Context) -> None:
        if self.block_updates:
            return
        self.block_updates = True

        node: 'NodeTransformProps' = self.node

        # DO THE CALCULATIONS HERE...
        if node:
            node.on_update_rect_pre(context, self)

        self.update_coords()

        # Do extra stuff per Node if needed...
        if node:
            node.on_update_rect_post(context, self)
            node.update_graphics(context)

        self.block_updates = False

    def update_coords(self) -> None:
        origin = Vector(self.origin)
        bot_left = Vector((
            int(origin.x - self.pivot[0] * self.dimensions[0]),
            int(origin.y - self.pivot[1] * self.dimensions[1])
        ))

        size = self.size

        coords = (
            Vector((bot_left.x, bot_left.y + size.y)),
            bot_left,
            Vector((bot_left.x + size.x, bot_left.y)),
            bot_left + size
        )

        self.coords = coords

        self.update_rotated()

    def update_rotated(self) -> None:
        if self.rotation != 0:
            origin = Vector(self.origin)
            self.coords_rotated = [
                rotate_point(Vector(co), origin, self.rotation) for co in self.coords
            ]
        else:
            self.coords_rotated = self.coords

    def update_from_coords(self, context: Context) -> None:
        self.block_updates = True

        self.dimensions = (
            int(self.x_max - self.x_min),
            int(self.y_max - self.y_min)
        )

        if self.rotation == 0:
            bot_left = self.bottom_left # from self.coords.
            self.origin = (
                int(bot_left.x + self.pivot[0] * self.dimensions[0]),
                int(bot_left.y + self.pivot[1] * self.dimensions[1])
            )
        self.update_rotated()

        if node := self.node:
            node.update_graphics(context)

        self.block_updates = False


    # ----- Properties --------------------------------

    can_update_origin_on_redimension: BoolProperty(default=True)

    block_updates: BoolProperty(
        name="Block Updates",
        description="Flag to Block Rect Transform updates",
        default=False,
        options={'HIDDEN'}
    )

    coords: FloatVectorProperty(
        name="Rect Coordinates",
        size=(4, 2), # Coordinates of the 4 points of the RectTransform.
        subtype='XYZ'
    )

    coords_rotated: FloatVectorProperty(
        name="Rotated Rect Coordinates",
        description="Rect Coordinates with Rotation applied",
        size=(4, 2), # Coordinates of the 4 points of the RectTransform.
        subtype='XYZ'
    )

    origin: IntVectorProperty( # old location
        name="Origin",
        description="Picker button origin location (actually its center with a 0.5 pivot in both XY axis) inside the NodeGraph 2D view",
        default=(0, 0),
        size=2,
        subtype='XYZ',
        update=update
    )

    pivot: FloatVectorProperty(
        name="Pivot",
        description="The pivot defines the alignment of the RectTransform. By default (0.5, 0.5) means the origin is centered",
        size=2,
        default=(0.5, 0.5),
        min=0.0, max=1.0,
        subtype='XYZ',
        update=update
    )

    rotation: FloatProperty(
        name="Rotation",
        description="Picker button rotation in the NodeGraph 2D view",
        default=0,
        soft_min=-pi/2,
        soft_max=pi/2,
        min=-pi*2,
        max=pi*2,
        subtype='ANGLE',
        unit='ROTATION',
        update=update
    )

    dimensions: IntVectorProperty(
        name="Dimensions",
        size=2,
        min=10,
        max=2000,
        default=(20, 20),
        subtype='XYZ',
        options={'HIDDEN'},
        update=update
    )

    edit_dimensions: IntVectorProperty(
        name="Dimensions",
        description="Picker button size in the NodeGraph 2D view",
        default=(20, 20),
        max=2000,
        min=10,
        size=2,
        subtype='XYZ',
        update=update_dimensions
    )

    @property
    def center(self) -> Vector:
        if self.pivot[0] == 0.5 and self.pivot[1] == 0.5:
            return Vector(self.origin)
        x, y = self.bottom_left
        w, h = self.dimensions
        w_div2 = int(w / 2)
        h_div2 = int(h / 2)
        return Vector((x - w_div2, y - h_div2))

    @property
    def position(self) -> Vector:
        ''' Wrapper for "bottom_left". '''
        return self.bottom_left

    @property
    def bottom_left(self) -> Vector:
        return Vector(self.coords[1])

    @property
    def bottom_right(self) -> Vector:
        return Vector(self.coords[2])

    @property
    def top_left(self) -> Vector:
        return Vector(self.coords[0])

    @property
    def top_right(self) -> Vector:
        return Vector(self.coords[3])

    @property
    def size(self) -> Vector:
        return Vector((max(self.dimensions[0], 1), max(self.dimensions[1], 1)))

    @property
    def x_min(self) -> float:
        return min(self.coords, key=lambda v: v[0])[0]

    @property
    def x_max(self) -> float:
        return max(self.coords, key=lambda v: v[0])[0]

    @property
    def y_min(self) -> float:
        return min(self.coords, key=lambda v: v[1])[1]

    @property
    def y_max(self) -> float:
        return max(self.coords, key=lambda v: v[1])[1]

    @property
    def min(self) -> Vector:
        return Vector((self.x_min, self.y_min))

    @property
    def max(self) -> Vector:
        return Vector((self.x_max, self.y_max))

    @property
    def coords_rotated_norm(self) -> list[Vector]:
        ''' Order: ``Top-Left``, ``Bottom-Left``, ``Bottom-Right``, ``Top-Right``. '''
        coords = self.coords_rotated
        min_x = min(coords, key=lambda v: v[0])[0]
        min_y = min(coords, key=lambda v: v[1])[1]
        min_off = Vector((min_x, min_y))
        return [Vector(co) - min_off for co in coords]

    @property
    def bound_box(self) -> list[Vector]:
        ''' Order: ``Top-Left``, ``Bottom-Left``, ``Bottom-Right``, ``Top-Right``. '''
        if self.rotation == 0:
            return [
                self.top_left,
                self.bottom_left,
                self.bottom_right,
                self.top_right
            ]
        coords = self.coords_rotated
        min_x = min(coords, key=lambda v: v[0])[0]
        max_x = max(coords, key=lambda v: v[0])[0]
        min_y = min(coords, key=lambda v: v[1])[1]
        max_y = max(coords, key=lambda v: v[1])[1]
        return [
            Vector((min_x, max_y)),
            Vector((min_x, min_y)),
            Vector((max_x, min_y)),
            Vector((max_x, max_y))
        ]

    @property
    def bound_box_norm(self) -> list[Vector]:
        ''' Order: ``Top-Left``, ``Bottom-Left``, ``Bottom-Right``, ``Top-Right``. '''
        bbox = self.bound_box
        bottom_left = bbox[0]
        return [co - bottom_left for co in bbox]

    @property
    def bound_box_size(self) -> Vector:
        coords = self.coords_rotated
        min_x = min(coords, key=lambda v: v[0])[0]
        max_x = max(coords, key=lambda v: v[0])[0]
        min_y = min(coords, key=lambda v: v[1])[1]
        max_y = max(coords, key=lambda v: v[1])[1]
        return Vector((
            max_x - min_x,
            max_y - min_y
        ))


    # ----------------------------------------
    ''' BBOX SETTERS. '''

    @x_min.setter
    def x_min(self, value: int) -> None:
        new_width = self.x_max - value
        ## print("Set[x_min]:", value, new_width)
        if new_width < 10:
            if new_width == self.dimensions[0]:
                return
            new_width = 10
            value = self.x_max - 10

        with CM_BlockUpdates(self):
            self.coords[0][0] = self.coords[1][0] = value

            self.dimensions[0] = int(new_width)

            if self.rotation == 0 and self.can_update_origin_on_redimension:
                self.origin[0] = int(self.coords[1][0] + self.pivot[0] * new_width)
            else:
                # This works and center the origin BUT... it doesn't center so that the coords stays the same.
                # rect_dir_v = (Vector(self.coords_rotated[2]) - Vector(self.coords_rotated[1])).normalized()
                # self.origin = (
                #     int(self.coords[1][0] + self.pivot[0] * (width  + rect_dir_v.x * delta_x_min)),
                #     int(self.coords[1][1] + self.pivot[1] * (height + rect_dir_v.y * delta_x_min))
                # )
                ## self.origin = (
                ##     int(self.coords_rotated[1][0] + self.pivot[0] * (width  + rect_dir_v.x * delta_x_min)),
                ##     int(self.coords_rotated[1][1] + self.pivot[1] * (height + rect_dir_v.y * delta_x_min))
                ## )

                pass
                '''
                width, height = self.dimensions

                origin_in_local = Vector((
                    self.pivot[0] * width,
                    self.pivot[1] * height
                ))
                rotation_angle = self.rotation
                rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
                rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

                self.origin = (
                    int(self.coords_rotated[1][0] + rotated_offset_x),
                    int(self.coords_rotated[1][1] + rotated_offset_y)
                )
                '''

            self.update_rotated()


    @x_max.setter
    def x_max(self, value: int) -> None:
        new_width = value - self.x_min
        if new_width < 10:
            if new_width == self.dimensions[0]:
                return
            new_width = 10
            value = self.x_min + 10
        with CM_BlockUpdates(self):
            self.coords[2][0] = self.coords[3][0] = value
            self.dimensions[0] = int(new_width)

            if self.rotation == 0 and self.can_update_origin_on_redimension:
                self.origin[0] = int(self.coords[1][0] + self.pivot[0] * new_width)

            else:
                pass
                '''
                width, height = self.dimensions

                origin_in_local = Vector((
                    self.pivot[0] * width,
                    self.pivot[1] * height
                ))
                rotation_angle = self.rotation
                rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
                rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

                self.origin = (
                    int(self.coords_rotated[1][0] + rotated_offset_x),
                    int(self.coords_rotated[1][1] + rotated_offset_y)
                )
                '''

                # self.update_coords()

            self.update_rotated()


    @y_min.setter
    def y_min(self, value: int) -> None:
        new_height = int(self.y_max - value)
        if new_height < 10:
            if new_height == self.dimensions[1]:
                return
            new_height = 10
            value = self.y_max - 10
        with CM_BlockUpdates(self):
            self.coords[1][1] = self.coords[2][1] = value

            height_diff = new_height - self.dimensions[1]
            self.dimensions[1] = new_height

            if self.rotation == 0 and self.can_update_origin_on_redimension:
                self.origin[1] = int(self.coords[1][1] + self.pivot[1] * new_height)
            else:
                pass
                '''
                width, height = self.dimensions

                origin_in_local = Vector((
                    self.pivot[0] * width,
                    self.pivot[1] * height
                ))
                rotation_angle = self.rotation
                rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
                rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

                self.origin = (
                    int(self.coords_rotated[1][0] + rotated_offset_x),
                    int(self.coords_rotated[1][1] + rotated_offset_y)
                )
                '''

            self.update_rotated()


    @y_max.setter
    def y_max(self, value: int) -> None:
        new_height = int(value - self.y_min)
        if new_height < 10:
            if new_height == self.dimensions[1]:
                return
            new_height = 10
            value = self.y_min + 10
        with CM_BlockUpdates(self):
            self.coords[0][1] = self.coords[3][1] = value

            self.dimensions[1] = new_height

            if self.rotation == 0 and self.can_update_origin_on_redimension:
                self.origin[1] = int(self.coords[1][1] + self.pivot[1] * new_height)
            else:
                pass
                '''
                width, height = self.dimensions

                origin_in_local = Vector((
                    self.pivot[0] * width,
                    self.pivot[1] * height
                ))
                rotation_angle = self.rotation
                rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
                rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

                self.origin = (
                    int(self.coords_rotated[1][0] + rotated_offset_x),
                    int(self.coords_rotated[1][1] + rotated_offset_y)
                )
                '''

            self.update_rotated()


    # ----------------------------------------

    def move(self, off_x, off_y) -> None:
        self.origin = (int(self.origin.x + off_x), int(self.origin.y + off_y))

    def move_to(self, loc) -> None:
        self.origin = (int(loc[0]), int(loc[1]))

    def resize(self, w, h) -> None:
        self.dimensions = (int(w), int(h))


    def get_point_relative(self, rel_x: float, rel_y: float, offset: Vector | None = None, apply_rotation: bool = True, rotate_from_origin: bool = False) -> Vector:
        p = self.bottom_left
        p.x += self.size.x * rel_x
        p.y += self.size.y * rel_y
        if offset is not None:
            p += offset
        if apply_rotation and self.rotation != 0:
            p = rotate_point(p, Vector(self.origin) if rotate_from_origin else self.bottom_left, self.rotation)
        return p

    def point_inside_rect(self, point: Vector) -> bool:
        return point_inside_rect(point, self.position, self.size, self.rotation, self.origin)

    def convert_abs_coord_to_rel_coord(self, region_point: Vector, context: Context | None = None) -> Vector:
        ''' Point should be inside rect
            If passing context, point should be in region space coordinates, otherwise in view space.
            Returned coords will be between 0 and 1.
            By default it uses its BoundingBox. '''
        bbox = self.bound_box
        p = region_point.copy()

        if context:
            if self.rotation != 0:
                o = get_node_editor_region_coord(context, Vector(self.origin))
                p = rotate_point(p, o, -self.rotation)

            bbox = [get_node_editor_region_coord(context, co) for co in bbox]
            scale = get_node_editor_zoom(context)
        else:
            scale = 1

        ## print(point, bbox)

        bbox_size = self.bound_box_size * scale
        p = p - bbox[1] # left bottom corner of the bounding box.
        p = Vector((
            p.x / bbox_size.x,
            p.y / bbox_size.y
        ))

        # if self.rotation != 0:
        #     p = rotate_point(p, Vector((0, 0)), self.rotation)
        return p


class NodeTransformProps:
    def on_update_rect_pre(self, context: Context, rect_transform: RectTransform) -> None:
        pass

    def on_update_rect_post(self, context: Context, rect_transform: RectTransform) -> None:
        pass

    rect_transform: PointerProperty(type=RectTransform)

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin') # old location
        layout.prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'dimensions')
        layout.prop(rect_transform, 'rotation')
        layout.prop(self, 'draw_depth')

        # layout.prop(self, 'scale')
