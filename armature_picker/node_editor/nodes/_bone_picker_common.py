from bpy.types import Context, Armature, Bone, Event, UILayout
from mathutils import Vector
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty

from ._transform_props import RectTransform
from ...gpu import draw
from ...utils.armature import deselect_all_bones_from_active



class APNODE_BonePicker_CommonProps:
    
    def get_bone_names(self, context: Context) -> tuple:
        if context.active_object is not None and context.active_object.type == 'ARMATURE':
            return tuple((bone.name, bone.name, "") for bone in context.active_object.data.bones)
        return (('NONE', "None", "",),)

    def get_bone_custom_properties(self, context: Context) -> None:
        if context.active_object is not None and self.use_ik_fk and context.active_object.type == 'ARMATURE':
            pose = context.active_object.pose
            if bone := pose.bones.get(self.bone_name, None):
                items = [(key, key, "") for (key, value) in bone.items() if not key.startswith('_RNA') and isinstance(value, bool)]
                if len(items) != 0:
                    return items
        return ((
            'NONE', "None", "",
        ),)

    # ----- UPDATES -----------------------------------

    def update_bone_name(self, context: Context) -> None:
        if self.label == '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()

    def update_ik_fk_idname(self, context: Context) -> None:
        if self.use_ik_fk and self.ik_fk_prop_idname == 'NONE':
            self.use_ik_fk = False
        self.update_dimensions(context)


    # ----- PROPERTIES --------------------------------

    bone_name: EnumProperty(
        name="Bone Name",
        description="Name of the bone to control",
        items=get_bone_names,
        update=update_bone_name
    )

    use_ik_fk: BoolProperty(default=False, name="Use IK/FK", description="This button picker controls a bone that has a IK/FK toggle")
    ik_fk_prop_idname: EnumProperty(
        name="IK/FK Property",
        description="Identifier of the Custom Property that controls the IK/FK for the bone",
        items=get_bone_custom_properties,
        update=update_ik_fk_idname
    )

    ik_fk_size: FloatProperty(
        name="IK/FK Size",
        description="Size of the IK/FK toggle",
        default=20,
        min=12,
        max=64,
        update=lambda node, ctx: node.update_graphics(ctx)
    )


    # ----- DRAW UI LAYOUT --------------------------------

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        if context.active_object is None or context.active_object.type not in {'ARMATURE'}:
            return
        if context.active_object.animation_data is None:
            layout.label(text="No animation data")
            return

        col = layout.column(align=False)
        col.use_property_decorate = True
        col.use_property_split = True
        if action := context.active_object.animation_data.action:
            bone = self.get_bone(context, from_pose_data=True)
            if bone is None:
                return

            drawn_attr = set()
            for fcu in action.fcurves:
                data_path: str = fcu.data_path
                if data_path.startswith('pose.bones'):
                    if self.bone_name == data_path.split('"')[1]:
                        attr = data_path.split('.')[-1]
                        if attr in drawn_attr:
                            continue
                        drawn_attr.add(attr)
                        col.prop(bone, attr)


    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        if context.active_object is None or context.active_object.type not in {'ARMATURE'}:
            return
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop_search(self, 'bone_name', context.active_object.pose, 'bones', text='', icon='BONE_DATA')

        row = layout.row(align=True, heading='IK/FK')
        row.prop(self, 'use_ik_fk', text='', expand=False)
        row.prop(self, 'ik_fk_prop_idname', text='')
        row = layout.row()
        row.enabled = self.use_ik_fk
        row.prop(self, 'ik_fk_size', text='Toggle Size')



class APNODE_BonePicker_Common(APNODE_BonePicker_CommonProps):
    draw_layer = 10


    def init(self, context):
        super().init(context)

        self.set_state('ik_fk_hovered', False)


    def get_ik_fk_state(self, context: Context) -> bool:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            return False
        if bone := self.get_bone(context, from_pose_data = True):
            if self.ik_fk_prop_idname in bone:
                return bool(bone[self.ik_fk_prop_idname])
        return False

    def toggle_ik_fk(self, context: Context) -> bool:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            return False
        if bone := context.active_pose_bone:
            if bone.name != self.bone_name:
                bone = context.active_object.pose.bones.get(self.bone_name, None)
                if bone is None:
                    return False
            if self.ik_fk_prop_idname in bone:
                bone[self.ik_fk_prop_idname] = not bool(bone[self.ik_fk_prop_idname])
        return False


    # ----- SELECT METHODS --------------------------------

    def get_bone(self, context: Context, from_pose_data: bool = False) -> Bone:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            return None
        armature: Armature = context.active_object.data
        if from_pose_data:
            bones = context.active_object.pose.bones
        else:
            bones = armature.bones if context.mode == 'POSE' else armature.edit_bones
        return bones.get(self.bone_name, None)

    def select_bone(self, context: Context, deselect_all: bool = True) -> None:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            return
        armature: Armature = context.active_object.data
        bones = armature.bones if context.mode == 'POSE' else armature.edit_bones
        bone: Bone
        if bone := self.get_bone(context):
            if deselect_all:
                deselect_all_bones_from_active(context)
            bone.select = True
            bones.active = bone

    # ------ ON HOVER --------------------------------

    def on_hover_exit(self, context: Context | None = None) -> None:
        self.set_state('ik_fk_hovered', False)


    # ----- INVOKE --------------------------------

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
            if self.get_state('ik_fk_hovered'):
                self.toggle_ik_fk(context)
                return
            self.select_node(context, deselect_all=not event.shift)
            self.select_bone(context, deselect_all=not event.shift)


    # ------ DRAWING --------------------------------

    def draw__pose(self, context, rect: RectTransform, style, wg_settings, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        if active:
            draw.box_ui(
                self, 'SELECT_CAGE',
                margin=2,
                line_thickness=2 * scale,
                color=(1.0, 1.0, .1, 1.0)
            )
