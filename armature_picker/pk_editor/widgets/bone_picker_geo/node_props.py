from bpy.types import Context, Object
from bpy.props import FloatProperty, EnumProperty, PointerProperty

from .wg_style import PG__BonePickerGeo__LocalStyle, PG__BonePickerGeo__Style
from .wg_settings import PG_BonePickerGeo_Settings
from armature_picker.pk_editor.widgets.bone_picker_geo.geometry import AP_PG_Geometry


class APNODE_BonePickerGeo_NodeProps:
    def get_style(self, theme) -> PG__BonePickerGeo__Style:
        return super().get_style(theme)

    style: PointerProperty(name="Style", type=PG__BonePickerGeo__LocalStyle)

    def get_settings(self, prefs_wg_settings) -> PG_BonePickerGeo_Settings:
        return super().get_settings(prefs_wg_settings)

    # UPDATE
    # ----------------------------------------------------------------

    def update_graphics(self, context: Context) -> None:
        super().update_graphics(context)
        self.geometry.update_batch(self)

    def update_dimensions(self, context: Context) -> None:
        scale = self.geo_scale
        dim = self.geometry.dimensions
        self.rect_transform.dimensions = (
            int(dim[0] * scale),
            int(dim[1] * scale)
        )
        self.update_graphics(context)

    def load_shape_from_geometry(self, context: Context, ob: Object, scale: float = None) -> None:
        self.geometry.update(self, ob, update_batch=True)
        if scale is not None:
            # To avoid twice updates.
            self.geo_scale = scale
        else:
            self.update_dimensions(context)


    # PROPERTIES
    # ----------------------------------------------------------------

    # object: PointerProperty(
    #     name="Mesh Object",
    #     description="Object that will be used to render the bone picker button graphics.\nTrace your mesh in the X/Y coordinates and ensure there is no loose parts",
    #     type=Object,
    #     poll=lambda node, ob: ob.type == 'MESH' and ob.dimensions[-1] == 0
    # )

    geometry: PointerProperty(type=AP_PG_Geometry)

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
            # ('FAST', 'Fast', "Use bounding box of the geometry"),
            ('CONVEX', "Convex Hull", "Creates a convex hull from the given geometry object"),
            ('PRECISE', "Precise", "The most precise but slower method. Good for complex geometry with holes and multiple parts")
        ),
        default='CONVEX',
        # update=update_dimensions
    )
