from bpy.types import Context, Armature, Bone, Event, UILayout, AnyType
from mathutils import Vector
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty

from armature_picker.utils.event import Mouse, EventType, EventValue
from armature_picker.utils.operator import OpsReturn
from ._transform_props import RectTransform
from ...gpu import draw
from ...utils.operator import OpsReturn
from ...utils.math import clamp, map_value, pi
from math import degrees



class APNODE_Slider_CommonStyle:
    def update_handle_pos(self, context: Context):
        self.set_state('dirty_handle_pos', True)
        context.area.tag_redraw()


    show_handle: BoolProperty(
        name="Show Handle",
        description="Show slider handle",
        default=True,
        update=update_handle_pos
    )

    handle_type: EnumProperty(
        name="Handle Type",
        items=(
            ('CIRCLE', "Circle", "Circular shape", 'RADIOBUT_ON', 0),
            ('LINE', "Line", "Line shape", 'FIXED_SIZE', 1),
        ),
        default='CIRCLE',
        update=update_handle_pos
    )

    bar_line_thickness: FloatProperty(
        name="Bar Thickness",
        description="Bar Line type thickness",
        default=1.5,
        min=1,
        max=5,
        update=lambda node, ctx: node.update_graphics(ctx)
    )

    bar_type: EnumProperty(
        name="Bar Type",
        items=(
            ('FILL', "Fill", "Fill shape"),
            ('LINE', "Line", "Line shape"),
        ),
        default='FILL',
        update=lambda node, ctx: node.update_graphics(ctx)
    )

    color: FloatVectorProperty(
        name="Color",
        description="Slider base color",
        default=(.32, .32, .32, .9),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    fill_color: FloatVectorProperty(
        name="Fill Color",
        description="Slider fill color",
        default=(.24, .54, 1.0, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    handle_color: FloatVectorProperty(
        name="Handle Color",
        description="Slider handle color",
        default=(.64, .64, .64, 1),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    roundness: FloatProperty(
        name="Roundness",
        description="Roundness of the button",
        min=0.2,
        max=1,
        default=1,
        precision=2
    )

    outline_thickness: FloatProperty(
        name="Outline Thickness",
        description="Ouline thickness of the button",
        min=0,
        max=20,
        default=1.5,
        precision=1
    )

    outline_color: FloatVectorProperty(
        name="Outline Color",
        description="Outline Color of the button",
        default=(.8, .6, .2, .9),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )


    def draw_styles(self, layout: UILayout) -> None:
        col = layout.column()
        col.prop(self, 'roundness')
        col.prop(self, 'outline_thickness')

        col.separator()

        col.prop(self, 'bar_type')
        col.prop(self, 'color')
        if self.bar_type == 'FILL':
            col.prop(self, 'fill_color')
        elif self.bar_type == 'LINE':
            col.prop(self, 'bar_line_thickness')

        col.separator()

        row = col.row(align=True, heading='Handle')
        row.prop(self, 'show_handle', text='')
        _row = row.row(align=True)
        _row.enabled = self.show_handle
        _row.prop(self, 'handle_color',  text='')
        _row.prop(self, 'handle_type',  text='', icon_only=True)



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


    def get_bone_custom_properties(self, context: Context) -> None:
        if context.active_object is None:
            return ((
                'NONE', "None", "",
            ),)
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


    def get_data_and_datapath(self, context: Context) -> tuple[AnyType, str, bool]:
        is_custom_datapath: bool = False
        is_custom_prop: bool = False

        if self.data_source == 'BONE':
            data = self.get_bone(context, from_pose_data=True)
            if self.bone_data_source == 'ATTR':
                data_path = self.bone_attr
            elif self.bone_data_source == 'CUSTOM_PROPERTY':
                is_custom_prop = True
                data_path = f'["{self.bone_custom_property}"]'

        elif self.data_source == 'DATA_PATH':
            is_custom_datapath = True
            data = context.active_object
            data_path = self.data_path

        return (data, data_path, is_custom_datapath, is_custom_prop)


    def get_value(self, context: Context) -> float | int | None:
        data, data_path, is_custom_datapath, is_custom_prop = self.get_data_and_datapath(context)
        if data is None or data_path == '':
            print("WTF", data, data_path)
            return None

        try:
            value = data.path_resolve(data_path, True)
        except Exception as e:
            print(e)
            return None

        ## print(value)
        return value


    def set_value(self, context: Context, new_value: int | float) -> None:
        if not isinstance(new_value, (float, int)):
            return

        data, full_data_path, is_custom_datapath, is_custom_prop = self.get_data_and_datapath(context)
        if data is None or full_data_path == '':
            return

        if self.clamp_slider:
            new_value = clamp(new_value, *self.range)

        #if is_custom_datapath:
        #    if full_data_path.endswith(']'):
        #        # Custom Property...
        #        start_custom_prop = full_data_path.rindex('[')
        #        data_path = full_data_path[:start_custom_prop]
        #        custom_prop = full_data_path[start_custom_prop:]

        if is_custom_prop:
            attr = full_data_path
            value = self.get_value(context)
            if isinstance(value, int):
                # Ensure it is integer value to avoid mutating custom property type.
                new_value = int(new_value)
        else:
            split = full_data_path.split('.')
            data_path = '.'.join(split[:-1])
            attr = split[-1]
            data = data.path_resolve(data_path, True)

        setattr(data, attr, new_value)


    # ----- UPDATES -----------------------------------

    def update_bone_name(self, context: Context) -> None:
        if self.bone_name != '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()

    def update_bone_custom_property(self, context: Context) -> None:
        pass


    # ----- PROPERTIES --------------------------------

    data_source: EnumProperty(
        name="Data Source",
        description="Where to get data from... To control its value from the slider",
        items=(
            ('BONE', 'Bone', "Use a Bone as source. Control a pose bone built-in property or a custom property"),
            ('DATA_PATH', 'Data Path', "Use a custom data path to the data source and its property"),
        ),
        default='BONE'
    )

    bone_name: EnumProperty(
        name="Bone Name",
        description="Name of the bone to control",
        items=lambda node, ctx: tuple((bone.name, bone.name, "") for bone in ctx.active_object.data.bones),
        update=update_bone_name
    )

    bone_data_source: EnumProperty(
        name="Bone Data Source",
        description="Where to get data from... To control its value from the slider",
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
        description="RMB over any property and select 'copy full data path', then paste it here (only floats or integers are supported)",
        default='',
    )

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


    # ----- DRAW UI LAYOUT --------------------------------

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        # Draw data_path property field...
        pass

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
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
            row = layout.row()
            try:
                if self.data_path != '':
                    context.active_object.path_resolve(self.data_path, True)
            except Exception as e:
                row.alert = True
            row.prop(self, 'data_path')


    def draw_slider_constraints_props(self, layout: UILayout) -> None:
        layout.prop(self, 'clamp_slider')

        col = layout.column(align=True)
        col.enabled = self.clamp_slider
        col.prop(self, 'unit_type')
        if self.unit_type == 'VALUE':
            col.prop(self, 'min_value')
            col.prop(self, 'max_value')
        elif self.unit_type == 'ANGLE':
            col.prop(self, 'min_angle')
            col.prop(self, 'max_angle')

        col = layout.column(align=True)
        col.enabled = not self.clamp_slider
        col.prop(self, 'step')



class APNODE_Slider_CommonNode(APNODE_Slider_CommonStyle):
    draw_layer = 11


    @property
    def dirty_handle_pos(self) -> bool:
        return self.get_state('dirty_handle_pos', True)

    @dirty_handle_pos.setter
    def dirty_handle_pos(self, state: bool) -> None:
        self.set_state('dirty_handle_pos', state)


    def init(self, context):
        super().init(context)

        self.dirty_handle_pos = True
        self.rect_transform.dimensions = (100, 12)


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

    def draw__edit(self, context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active or selected:
            draw.box_ui(
                self, 'BOX_ACTIVE',
                line_thickness=2 * scale,
                color=(1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
            )

    # def draw__pose(self, context, rect: RectTransform, scale: float, active: bool, selected: bool, hovered: bool) -> None:
    #     if active:
    #         draw.box_ui(
    #             self, 'BOX_ACTIVE',
    #             line_thickness=(1.5 * scale),
    #             color=(1.0, 1.0, .1, 1.0)
    #         )


    # ----- TRANSFORM -----------------------------------------------------------

    def update_dimensions(self, context: Context) -> None:
        # on 'edit_dimensions' edit...
        rect = self.rect_transform
        w, h = rect.edit_dimensions

        if self.bar_type == 'LINE':
            if h > 15:
                rect.edit_dimensions = (w, 15)
                return

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
