import bpy
from bpy.types import Context
from bpy.props import EnumProperty

from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_check
from armature_picker.pk_editor.widgets.bone_picker_geo.node import APNODE_BonePickerGeo


items = [('NONE', 'None', ""),]


class LoadCustomShapeFromGeometry(ACK.Type.OPS.SEARCH_MENU):
    label = 'Load Custom Shape From Geometry'
    tooltip = "Use geometry shape as a custom shape for a Custom-Shape BonePicker"

    def get_objects(self, _context: Context):
        global items
        new_items = tuple((ob.name, ob.name, '') for ob in bpy.data.objects if ob.type == 'MESH' and ob.dimensions[-1] == 0 and len(ob.data.polygons) != 0 and len(ob.data.polygons) <= 100)
        items = new_items if len(new_items) != 0 else [('NONE', 'None', ""),]
        return items

    object_name: EnumProperty(
        name="Mesh Object",
        description="Object that will be used to render the bone picker button graphics.\nTrace your mesh in the X/Y coordinates and ensure there is no loose parts",
        items=get_objects,
        default=None
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=False, use_picker_editor=True, use_active_node=APNODE_BonePickerGeo)

    def action(self, context: Context) -> None:
        if ob := bpy.data.objects.get(self.object_name, None):
            context.space_data.node_tree.nodes.active.load_shape_from_geometry(context, ob)
