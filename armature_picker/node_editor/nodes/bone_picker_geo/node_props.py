from bpy.types import Context, UILayout, Armature, Object
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from math import ceil

from ....utils.math import clamp
from ....gpu import draw_geo
from armature_picker.prefs.styles import BonePickerGeo_LocalStyle, BonePickerGeo_Style
from armature_picker.prefs.settings import BonePickerGeo_Settings
from armature_picker.data.pg.geometry import AP_PG_Geometry


class APNODE_BonePickerGeo_NodeProps:
    def get_style(self, theme) -> BonePickerGeo_Style:
        return super().get_style(theme)

    style: PointerProperty(name="Style", type=BonePickerGeo_LocalStyle)

    def get_settings(self, prefs_wg_settings) -> BonePickerGeo_Settings:
        return super().get_settings(prefs_wg_settings)

    # UPDATE
    # ----------------------------------------------------------------

    def update_dimensions(self, context: Context) -> None:
        self.dirty = True
        draw_geo.Geometry.get(self)

        scale = self.geo_scale
        dim = self.geometry.dimensions
        self.rect_transform.dimensions = (
            int(dim[0] * scale),
            int(dim[1] * scale)
        )

        self.update_graphics(context)

    def update_object(self, context: Context) -> None:
        if self.object is None:
            return

        self.dirty_geo = True
        self.geometry.update(self.object)
        self.update_dimensions(context)
        self.dirty_geo = False

        self.object = None


    # PROPERTIES
    # ----------------------------------------------------------------

    geometry: PointerProperty(type=AP_PG_Geometry)

    object: PointerProperty(
        name="Mesh Object",
        description="Object that will be used to render the bone picker button graphics.\nTrace your mesh in the X/Y coordinates and ensure there is no loose parts",
        type=Object,
        poll=lambda node, ob: ob.type == 'MESH' and ob.dimensions[-1] == 0,
        update=update_object
    )

    geo_scale: FloatProperty(
        name="Geometry Scale",
        default=20,
        min=1.0,
        max=1000,
        update=update_dimensions
    )

    geo_precision: EnumProperty(
        name="Precision",
        description="Method to use to determine if the cursor is hovering the geometry",
        items=(
            ('FAST', 'Fast', "Use bounding box of the geometry"),
            ('CONVEX', "Convex Hull", "Creates a convex hull from the given geometry object"),
            ('PRECISE', "Precise", "The most precise but slower method. Good for complex geometry with holes and multiple parts")
        ),
        default='CONVEX',
        # update=update_dimensions
    )


    def draw_object_props(self, layout: UILayout) -> None:
        layout.prop(self, 'object')
        layout.prop(self, 'geo_precision')
