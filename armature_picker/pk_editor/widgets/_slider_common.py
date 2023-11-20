from bpy.types import Context, Armature, Bone, Event, UILayout, AnyType, ID
from mathutils import Vector
import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty

from armature_picker.ops import Ops as AP_OPS
from armature_picker.utils.event import Mouse, EventType, EventValue
from armature_picker.utils.operator import OpsReturn
from ._transform_props import RectTransform
from ...gpu import draw
from ...utils.operator import OpsReturn
from ...utils.math import clamp, map_value, pi

from math import degrees
from dataclasses import dataclass


@dataclass
class PropertyData:
    id: ID
    data_path: str = ''
    attr: str | None = None
    # custom_data_prop: AnyType | Vector | None = None
    custom_property: str | None = None
    index: int = -1

    @property
    def full_data_path(self) -> str:
        if self.attr is not None:
            if self.data_path == '':
                return self.attr
            return self.data_path + '.' + self.attr
        return self.data_path

    def get_value(self) -> int | float:
        ## print("--------------------------\nID:", self.id)
        ## print("data_path:", self.data_path)
        ## print("attr:", self.attr)
        ## print("custom_property:", self.custom_property)
        ## print("index:", self.index)
        try:
            if self.full_data_path == '':
                data = self.id
            else:
                data = self.id.path_resolve(self.full_data_path, True)
            if self.index != -1:
                value = data[self.index]
            elif self.custom_property is not None:
                value = data[self.custom_property]
            else:
                value = data
        except Exception as e:
            print(e)
            return None

        if not isinstance(value, (int, float)):
            return None
        ## print("> get_value:", value)
        return value

    def set_value(self, new_value: int | float) -> None:
        ## print("--------------------------\n> set_value:", new_value)
        if self.custom_property is not None:
            curr_value = self.get_value()
            if isinstance(curr_value, int):
                # Ensure it is integer value to avoid mutating custom property type.
                new_value = int(new_value)

        if self.data_path == '':
            data = self.id
        else:
            data = self.id.path_resolve(self.data_path, True)

        if self.index != -1:
            ## print("\t> DATA:", data, self.index)
            data[self.index] = new_value
        elif self.custom_property is not None:
            ## print("\t> DATA:", data, self.custom_property)
            data[self.custom_property] = new_value
        else:
            ## print("\t> DATA:", data, self.attr)
            setattr(data, self.attr, new_value)


class APNODE_Slider_DataConstraintsProps:
    # ----- SELECT METHODS --------------------------------

    def get_bone(self, context: Context, from_pose_data: bool = False) -> Bone:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            print("Active object is not an Armature")
            return None
        armature: Armature = context.active_object.data
        if from_pose_data:
            bones = context.active_object.pose.bones
        else:
            bones = armature.bones if context.mode == 'POSE' else armature.edit_bones
        return bones.get(self.bone_name, None)


    def get_bone_names(self, context: Context) -> tuple:
        if context.active_object is not None and context.active_object.type == 'ARMATURE':
            return tuple((bone.name, bone.name, "") for bone in context.active_object.data.bones)
        return (('NONE', "None", "",),)

    def get_bone_custom_properties(self, context: Context) -> None:
        if context.active_object is not None and context.active_object.type == 'ARMATURE':
            pose = context.active_object.pose
            if bone := pose.bones.get(self.bone_name, None):
                custom_props = [
                    (key, key, "") for (key, value) in bone.items() if not key.startswith('_RNA') and isinstance(value, (float, int))
                ]
                if len(custom_props) != 0:
                    return custom_props
        return ((
            'NONE', "None", "",
        ),)


    def get_property_data(self, context: Context) -> PropertyData:
        prop_data = PropertyData(None)

        if self.data_source == 'BONE':
            prop_data.id = self.get_bone(context, from_pose_data=True)
            if self.bone_data_source == 'ATTR':
                if '.' in self.bone_attr:
                    split = self.bone_attr.split('.')
                    prop_data.attr = split.pop(-1)
                    prop_data.data_path = '.'.join(split)
                else:
                    prop_data.attr = self.bone_attr
            elif self.bone_data_source == 'CUSTOM_PROPERTY':
                if self.bone_custom_property == 'NONE':
                    prop_data.id = None # INVALID CUSTOM PROPERTY.
                else:
                    prop_data.custom_property = self.bone_custom_property

        elif self.data_source == 'DATA_PATH' and self.data_path != '':
            prop_data.id = context
            data_path: str = self.data_path
            if data_path.endswith(']'):
                start_index = data_path.rindex('[')
                if data_path[-2].isdigit():
                    prop_data.index = int(data_path[start_index+1:-1])
                else:
                    prop_data.custom_property = data_path[start_index+2:-2]
                prop_data.data_path = data_path[:start_index]
            else:
                split = data_path.split('.')
                prop_data.attr = split.pop(-1)
                prop_data.data_path = '.'.join(split)

        return prop_data if prop_data.id is not None else None


    def get_value(self, context: Context) -> float | int | None:
        if prop_data := self.get_property_data(context):
            return prop_data.get_value()
        return None

    def set_value(self, context: Context, new_value: int | float) -> None:
        if not isinstance(new_value, (float, int)):
            return

        prop_data = self.get_property_data(context)
        if prop_data is None:
            return

        if self.clamp_slider:
            new_value = clamp(new_value, *self.range)

        prop_data.set_value(new_value)


    # ----- UPDATES -----------------------------------

    def update_bone_name(self, context: Context) -> None:
        if self.bone_name != '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()

    def update_bone_custom_property(self, context: Context) -> None:
        pass

    def update_handle_pos(self, context: Context) -> None:
        self.set_state('dirty_handle_pos', True)
        context.region.tag_redraw()


    # ----- PROPERTIES --------------------------------

    data_source: EnumProperty(
        name="Data Source",
        description="Where to get child from... To control its value from the slider",
        items=(
            ('BONE', 'Bone', "Use a Bone as source. Control a pose bone built-in property or a custom property"),
            ('DATA_PATH', 'Data Path', "Use a custom child path to the child source and its property"),
        ),
        default='BONE'
    )

    bone_name: EnumProperty(
        name="Bone Name",
        description="Name of the bone to control",
        items=get_bone_names,
        update=update_bone_name
    )

    bone_data_source: EnumProperty(
        name="Bone Data Source",
        description="Where to get child from... To control its value from the slider",
        items=(
            ('ATTR', 'Attribute', "Control a pose bone attribute (location, rotation, scale)"),
            ('CUSTOM_PROPERTY', 'Custom Property', "Control a pose bone custom property (only floats or integers are supported)"),
        ),
        default='CUSTOM_PROPERTY'
    )

    bone_attr: EnumProperty(
        name="Attribute",
        description="Select a bone property to control",
        items=(
            # ('location.x', 'Location X', "Location in the X axis"),
            # ('location.y', 'Location Y', "Location in the Y axis"),
            # ('location.z', 'Location Z', "Location in the Z axis"),
            ('rotation_euler.x', 'Rotation (Euler) X', "Rotation in the X axis"),
            ('rotation_euler.y', 'Rotation (Euler) Y', "Rotation in the Y axis"),
            ('rotation_euler.z', 'Rotation (Euler) Z', "Rotation in the Z axis"),
            ('scale.x', 'Scale X', "Scale in the X axis"),
            ('scale.y', 'Scale Y', "Scale in the Y axis"),
            ('scale.z', 'Scale Z', "Scale in the Z axis"),
        ),
        default='rotation_euler.x'
    )

    bone_custom_property: EnumProperty(
        name="Custom Property",
        description="Identifier of the Custom Property that controls the IK/FK for the bone",
        items=get_bone_custom_properties,
        update=update_bone_custom_property
    )

    data_path: StringProperty(
        name="Data Path",
        description="RMB over any property and select 'copy full child path', then paste it here (only floats or integers are supported)",
        default=''
    )

    # data_path_index: IntProperty(default=-1)

    # -----

    clamp_slider: BoolProperty(
        name="Clamp Slider",
        description="Set minimum and maximum values to clamp possible slider values",
        default=True,
    )

    min_value: FloatProperty(
        name="Min Value",
        default=0.0,
        precision=2,
    )

    max_value: FloatProperty(
        name="Max Value",
        default=1.0,
        precision=2,
    )

    min_angle: FloatProperty(
        name="Min Angle",
        default=0,
        unit='ROTATION'
    )

    max_angle: FloatProperty(
        name="Max Angle",
        default=2*pi,
        unit='ROTATION'
    )

    step: FloatProperty(
        name="Step",
        description="Slider step value",
        default=0.1,
        soft_min=0.001,
        soft_max=1000
    )

    unit_type: EnumProperty(
        name="Unit Type",
        items=(
            ('VALUE', "Value", "Just a value (default)"),
            ('ANGLE', "Angle", "Just an angle value"),
        ),
        default='VALUE'
    )

    @property
    def range(self) -> tuple[float, float]:
        if self.unit_type == 'VALUE':
            return (self.min_value, self.max_value)
        if self.unit_type == 'ANGLE':
            return (self.min_angle, self.max_angle)


    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        # layout.prop(self, 'clamp_slider')

        col = layout.column(align=True)
        # col.enabled = self.clamp_slider
        col.prop(self, 'unit_type')
        if self.unit_type == 'VALUE':
            col.prop(self, 'min_value')
            col.prop(self, 'max_value')
        elif self.unit_type == 'ANGLE':
            col.prop(self, 'min_angle')
            col.prop(self, 'max_angle')

        # col = layout.column(align=True)
        # col.enabled = not self.clamp_slider
        # col.prop(self, 'step')


    def draw_ui__edit(self, context: Context, layout: UILayout, dimension: str = 'NONE') -> None:
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.row().prop(self, 'data_source', expand=True)

        if self.data_source == 'BONE':
            layout.prop(self, 'bone_name', text='Bone', icon='BONE_DATA')

            if self.bone_name and self.bone_name != 'NONE':
                layout.row().prop(self, 'bone_data_source', expand=True, text=" ")

                if self.bone_data_source == 'ATTR':
                    layout.prop(self, 'bone_attr', text=" ")
                elif self.bone_data_source == 'CUSTOM_PROPERTY':
                    layout.prop(self, 'bone_custom_property', text=" ")

        elif self.data_source == 'DATA_PATH':
            self.draw_ui_data_path(layout, context, dimension=dimension)

        if hasattr(self, 'show_text_value'):
            layout.separator()
            layout.prop(self, 'show_text_value')

    def draw_ui_data_path(self, layout: UILayout, context: Context, dimension: str = 'NONE') -> None:
        if AP_OPS.PickLayoutProperty.operator.is_modal_running: # GLOBALS.get_addon_global_value('IS_PICKING_DATAPATH', False):
            box = layout.box()
            col = box.column(align=True)
            col.label(text='', icon='INFO')
            col.alert = True
            col.label(text='Right Click a Slider-Like Property')

        else:
            col = layout.column(align=True)
            col.label(text="Property Data-Path")
            row = col.row(align=True)
            row.use_property_split = False
            try:
                if self.data_path != '':
                    context.path_resolve(self.data_path, True)
            except Exception as e:
                row.alert = True
            row.prop(self, 'data_path', text='')
            AP_OPS.PickLayoutProperty.draw_in_layout(row, label='', icon='EYEDROPPER', op_props={'dimension': dimension})


class APNODE_Slider_CommonNode:
    draw_layer = 11

    show_text_value: BoolProperty(
        name="Show Value",
        description="Show text value",
        default=True
    )

    @property
    def dirty_handle_pos(self) -> bool:
        return self.get_state('dirty_handle_pos', True)

    @dirty_handle_pos.setter
    def dirty_handle_pos(self, state: bool) -> None:
        self.set_state('dirty_handle_pos', state)


    def init(self, context):
        super().init(context)

        self.dirty_handle_pos = True


    # ------ ON HOVER --------------------------------


    # ----- INVOKE --------------------------------

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            ## print("PRESS!")
            value = self.get_value(context)
            if value is None:
                ## print("KK VALUE")
                return OpsReturn.CANCEL
            self.value = value
            self.backup_value = value
            return OpsReturn.RUN
        return OpsReturn.FINISH


    # ----- MODAL --------------------------------

    def modal_exit__pose(self, context: Context, cancel: bool) -> None:
        if cancel:
            self.set_value(context, self.backup_value)
            self.update_handle_pos(context)

        del self.backup_value
        del self.value


    # ------ DRAWING --------------------------------


    # ----- DRAW UI LAYOUT --------------------------------

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        # Draw data_path property field...
        pass


    # ----- TRANSFORM -----------------------------------------------------------

    def update_dimensions(self, context: Context) -> None:
        # on 'edit_dimensions' edit...
        rect = self.rect_transform
        w, h = rect.edit_dimensions

        # if self.bar_type == 'LINE':
        #     if h > 15:
        #         rect.edit_dimensions = (w, 15)
        #         return

        if w < 20:
            rect.edit_dimensions = (20, 10)
            return

        t = w / h
        if t < 2:
            rect.edit_dimensions = (w, int(w * 0.5))
            return

        rect.dimensions = rect.edit_dimensions

    def draw_transform(self, layout: UILayout, rect_transform: RectTransform) -> None:
        layout.prop(rect_transform, 'origin')
        layout.prop(rect_transform, 'pivot')
        layout.prop(rect_transform, 'edit_dimensions', text='Size')
        layout.prop(rect_transform, 'rotation')
        layout.prop(self, 'draw_depth')



class APNODE_Slider_Common(APNODE_Slider_CommonNode, APNODE_Slider_DataConstraintsProps):
    pass
