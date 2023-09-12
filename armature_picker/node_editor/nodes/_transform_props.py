from bpy.types import Context, UILayout, PropertyGroup, Node, NodeTree
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, IntVectorProperty, EnumProperty, PointerProperty
from mathutils import Vector

from math import pi

from ...utils.geometry import rotate_point


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
        if node: node.on_update_rect_pre(context, self)

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

        if self.rotation != 0:
            self.coords_rotated = [
                rotate_point(co, origin, self.rotation) for co in coords
            ]
        else:
            self.coords_rotated = coords

        self.coords = coords

        # Do extra stuff per Node if needed...
        if node: node.on_update_rect_post(context, self)

        if node: node.update_graphics(context)

        self.block_updates = False


    # ----- Properties --------------------------------

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
        default=(20, 20),
        subtype='XYZ',
        options={'HIDDEN'},
        update=update
    )

    edit_dimensions: IntVectorProperty(
        name="Dimensions",
        description="Picker button size in the NodeGraph 2D view",
        default=(20, 20),
        min=20,
        size=2,
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
        return Vector(Vector(self.dimensions))

    @property
    def bound_box(self) -> list[Vector]:
        ''' Order: ``Bottom-Left``, ``Bottom-Right``, ``Top-Left``, ``Top-Right``. '''
        if self.rotation == 0:
            return [
                self.bottom_left,
                self.bottom_right,
                self.top_left,
                self.top_right
            ]
        coords = self.coords_rotated
        min_x = min(coords, key=lambda v: v[0])
        max_x = max(coords, key=lambda v: v[0])
        min_y = min(coords, key=lambda v: v[1])
        max_y = max(coords, key=lambda v: v[1])
        return [
            Vector((min_x, min_y)),
            Vector((max_x, min_y)),
            Vector((min_x, max_y)),
            Vector((max_x, max_y))
        ]

    @property
    def bound_box_norm(self) -> list[Vector]:
        bbox = self.bound_box
        bottom_left = bbox[0]
        return [co - bottom_left for co in bbox]

    @property
    def bound_box_size(self) -> Vector:
        coords = self.coords_rotated
        min_x = min(coords, key=lambda v: v[0])
        max_x = max(coords, key=lambda v: v[0])
        min_y = min(coords, key=lambda v: v[1])
        max_y = max(coords, key=lambda v: v[1])
        return Vector((
            max_x - min_x,
            max_y, min_y
        ))

    def move(self, off_x, off_y) -> None:
        self.origin = (int(self.origin.x + off_x), int(self.origin.y + off_y))

    def move_to(self, loc) -> None:
        self.origin = (int(loc[0]), int(loc[1]))

    def resize(self, w, h) -> None:
        self.dimensions = (int(w), int(h))


    def get_point_relative(self, rel_x: float, rel_y: float, apply_rotation: bool = True) -> Vector:
        p = self.bottom_left
        p.x += self.size.x * rel_x
        p.y += self.size.y * rel_y
        if apply_rotation and self.rotation != 0:
            p = rotate_point(p, self.bottom_left, self.rotation)
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
