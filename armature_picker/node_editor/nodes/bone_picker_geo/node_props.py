from bpy.types import Context, UILayout, Armature, Object
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from math import ceil

from ....utils.math import clamp

from ....gpu import draw_geo



class APNODE_BonePickerGeo_NodeProps:

    # UPDATE
    # ----------------------------------------------------------------

    def update_dimensions(self, context: Context) -> None:
        if self.object is None:
            return

        self.dirty = True
        draw_geo.Geometry.get(self)

        context.area.tag_redraw()

    def update_object(self, context: Context) -> None:
        if self.object is None:
            return
        
        scale = self.geo_scale
        dim = self.object.dimensions
        self.rect_transform.dimensions = (
            int(dim[0] * scale),
            int(dim[1] * scale)
        )

        self.color = self.object.color

        self.dirty_geo = True
        self.update_dimensions(context)
        self.dirty_geo = False


    # PROPERTIES
    # ----------------------------------------------------------------

    object: PointerProperty(
        name="Mesh Object",
        description="Object that will be used to render the bone picker button graphics.\nTrace your mesh in the X/Y coordinates and ensure there is no loose parts",
        type=Object,
        poll=lambda node, ob: ob.type == 'MESH' and ob.dimensions[-1] == 0,
        update=update_object
    )

    geo_scale: FloatProperty(
        name="Geometry Scale",
        default=10,
        min=1.0,
        max=1000,
        update=update_object
    )

    geo_precision: EnumProperty(
        name="Precision",
        description="Method to use to determine if the cursor is hovering the geometry",
        items=(
            ('FAST', 'Fast', "Use bounding box of the geometry"),
            ('CONVEX', "Convex Hull", "Creates a convex hull from the given geometry object"),
            ('PRECISE', "Precise", "The most precise but slower method. Good for complex geometry with holes and multiple parts")
        ),
        default='PRECISE',
        update=update_dimensions
    )


    def draw_object_props(self, layout: UILayout) -> None:
        layout.prop(self, 'object')
        layout.prop(self, 'geo_precision')
