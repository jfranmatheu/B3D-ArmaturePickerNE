import bpy
from bpy.types import Context, Event, Operator, Object
from bpy.props import EnumProperty, PointerProperty

from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn
from armature_picker.pk_editor.widgets.bone_picker_geo.node import APNODE_BonePickerGeo

items = [('NONE', 'None', ""),]

class AP_OT_load_custom_shape_from_geometry(Operator):
    bl_idname = 'armature_picker.load_custom_shape_from_geometry'
    bl_label = 'Load Custom Shape From Geometry'
    bl_description = "Use geometry shape as a custom shape for a Custom-Shape BonePicker"
    bl_property = 'object_name'

    def get_objects(self, context):
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

    #def draw(self, context: Context):
    #    # self.layout.operator_enum('armature_picker.load_custom_shape_from_geometry', 'object_name')
    #    # WHAT I WANT, BUT... IT TAKES ALL OBJECTS WITHOUT FILTERING... :(
    #    # self.layout.prop_search(self, 'object_name', bpy.child, 'objects')
    #    self.layout.prop(self, 'object_name')

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=False, use_picker_editor=True, use_active_node=APNODE_BonePickerGeo)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        self.object_name
        if res := context.window_manager.invoke_search_popup(self):
            return res
        return OpsReturn.UI

    def execute(self, context: Context) -> OpsReturn:
        ob = bpy.data.objects.get(self.object_name, None)
        if ob is None:
            return OpsReturn.CANCEL
        context.space_data.node_tree.nodes.active.load_shape_from_geometry(context, ob)
        return OpsReturn.FINISH
