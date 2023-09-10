from bpy.types import Context, UILayout, Armature
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from blf import size as set_text_size, dimensions as get_text_dimensions



class APNODE_BonePicker_NodeProps:
    def get_bone_custom_properties(self, context: Context) -> None:
        pose = context.active_object.pose
        if bone := pose.bones.get(self.bone_name, None):
            return [
                (key, key, "") for key in bone.keys() if not key.startswith('_RNA')
            ]
        else:
            return ((
                'NONE', "None", "",
            ),)

    def update_ik_fk_idname(self, context: Context) -> None:
        if self.use_ik_fk and self.ik_fk_prop_idname == 'NONE':
            self.use_ik_fk = False
        self.update_dimensions(context)

    def update_dimensions(self, context: Context) -> None:
        if self.fit_to_text and self.label == '':
            return

        if self.fit_to_text:
            ui_scale = context.preferences.system.ui_scale
            padding = 4 * ui_scale
            padding *= 2

            self.rect_transform.dimensions = (
                int(self.label_dimensions[0] + padding),
                int(self.label_dimensions[1] + padding)
            )

        else:
            # USER-EDITED-DIMENSIONS: self.edit_dimensions
            # INTERNAL DIMENSIONS: self.dimensions
            self.rect_transform.dimensions = (
                int(max(self.edit_dimensions[0] * self.scale[0], 10)),
                int(max(self.edit_dimensions[1] * self.scale[1], 10))
            )


    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_label(self, context: Context) -> None:
        set_text_size(0, self.text_size)
        self.label_dimensions = get_text_dimensions(0, self.label)

        self.update_dimensions(context)
        self.dirty_label = True
        self.update_graphics(context)

    def update_bone_name(self, context: Context) -> None:
        if self.label == '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    use_ik_fk: BoolProperty(default=False, name="Use IK/FK", description="This button picker controls a bone that has a IK/FK toggle")
    ik_fk_prop_idname: EnumProperty(
        name="IK/FK Property",
        description="Identifier of the Custom Property that controls the IK/FK for the bone",
        items=get_bone_custom_properties,
        update=update_ik_fk_idname
    )

    label_dimensions: FloatVectorProperty(
        name="Label Dimensions",
        min=0,
        size=2,
        subtype='XYZ',
        options={'HIDDEN'}
    )

    label: StringProperty(
        name="Label",
        description="Button label",
        update=update_label,
        options={'TEXTEDIT_UPDATE'}
    )

    bone_name: StringProperty(
        name="Bone Name",
        description="Name of the bone to control",
        update=update_bone_name
    )


    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        if context.active_object.animation_data is None:
            layout.label(text="No animation data")
            return

        col = layout.column(align=False)
        col.use_property_decorate = True
        col.use_property_split = True
        if action := context.active_object.animation_data.action:
            drawn_attr = set()
            for fcu in action.fcurves:
                data_path: str = fcu.data_path
                if data_path.startswith('pose.bones'):
                    if self.bone_name == data_path.split('"')[1]:
                        attr = data_path.split('.')[-1]
                        if attr in drawn_attr:
                            continue
                        drawn_attr.add(attr)
                        col.prop(self.get_bone(context, from_pose_data=True), attr)
                # print(fcu.data_path + " channel " + str(fcu.array_index))
                # for keyframe in fcu.keyframe_points:
                #     print(keyframe.co) #coordinates x,y

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'bone_name', text='Bone')

        layout.separator()

        row = layout.row(align=True, heading='IK/FK')
        row.prop(self, 'use_ik_fk', text='', expand=False)
        row.prop(self, 'ik_fk_prop_idname', text='')


    def draw_label_props(self, layout: UILayout) -> None:
        layout.prop(self, 'label')

        layout.separator()

        layout.prop(self, 'text_size')
        layout.prop(self, 'text_alignment')
        layout.prop(self, 'fit_to_text')
